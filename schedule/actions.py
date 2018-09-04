import codecs
import csv
from copy import copy
from datetime import date, datetime, time, timedelta
from math import floor

import json
import yaml
from django.contrib import messages
from django.utils.text import slugify
from icalendar import Calendar, Event, vCalAddress, vText
from pytz import timezone

from cfp.models import Proposal
from schedule.models import Cache, Room, Slot, SlotEvent


def get_time(seconds):
    hour = floor(seconds / (60 * 60))
    minute = int((seconds - (hour * 60 * 60)) / 60)

    return time(hour=hour, minute=minute)


def import_schedule(f, request):
    SlotEvent.objects.all().delete()

    reader = csv.reader(codecs.iterdecode(f, 'utf-8'))
    for i, (event_index, event, slot_index, slot_text) in enumerate(reader):
        if i == 0:
            continue
        slot_date, slot_time, *room = slot_text.split(' ')
        room = ' '.join(room)

        try:
            activity = Proposal.objects.get(title=event)
        except Proposal.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Couldn't find {event}")
            continue

        room = Room.objects.get(name=room)

        try:
            slot = Slot.objects.get(room=room, date=slot_date, time=slot_time)
            ical_id = ('%s-%s' % (activity.proposal_id, slot.date.strftime('%a'))
                       if activity.conference_event else activity.proposal_id).lower()
            SlotEvent.objects.get_or_create(
                activity=activity,
                slot=slot,
                ical_id=ical_id
            )

            if activity.session_type == 'workshop':
                slot_time_plus_91_mins = datetime.strptime(slot_time, '%H:%M:%S') + timedelta(minutes=91)
                slot = Slot.objects.filter(room=room, date=slot_date, time__gt=slot_time_plus_91_mins).first()
                SlotEvent.objects.get_or_create(
                    activity=activity,
                    slot=slot,
                    ical_id=ical_id
                )

        except Slot.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Couldn't find {room} on {slot_date} at {slot_time}")

    try:
        Cache.objects.get(key='schedule').delete()
    except Cache.DoesNotExist:
        pass


def import_timetable(timetable_f, unbounded_f, request):

    timetable = yaml.load(timetable_f.read())
    unbounded = yaml.load(unbounded_f.read())

    Slot.objects.filter(scheduler_linked=True).all().delete()

    for room_name, dates in timetable.items():
        room = Room.objects.get(name=room_name)
        for day, sessions in dates.items():
            for session_name, slots in sessions.items():
                for slot in slots:

                    slot = Slot(
                        room=room,
                        date=day,
                        session_name=None if session_name == 'None' else session_name,
                        time=get_time(slot['starts_at']),
                        duration=timedelta(minutes=slot['duration']),
                        event_type=slot['event_type'],
                        visible=True,
                        scheduler_linked=True
                    )

                    slot.save()

            # Add unbounded slots
            for item in unbounded:
                for slot_name, slot in item.items():

                    slot = Slot(
                        room=room,
                        date=day,
                        time=get_time(slot['starts_at']),
                        duration=timedelta(minutes=slot['duration']),
                        visible=True,
                        scheduler_linked=True
                    )

                    slot.save()


def generate_schedule_page_data():

    days = [date(2018, 9, 15), date(2018, 9, 16), date(2018, 9, 17), date(2018, 9, 18), date(2018, 9, 19)]

    all_sessions = {}

    for day in days:

        rooms_for_day_query = Slot.objects.filter(
            date=day
        ).distinct(
            'room'
        )

        rooms_for_day = [x.room for x in rooms_for_day_query]
        room_names_for_day = [x.name for x in rooms_for_day]

        times_for_day_query = Slot.objects.filter(
            date=day
        ).distinct(
            'time'
        ).values(
            'time'
        )
        times_for_day = [x['time'] for x in times_for_day_query]

        # lists of sessions, one list per time
        matrix = []

        # Make blank matrix
        for time_ in times_for_day:
            slot_events_for_time = SlotEvent.objects.filter(
                slot__date=day,
                slot__time=time_
            ).order_by(
                'slot__room__name'
            ).all()

            sessions = []

            for i, room in enumerate(rooms_for_day):
                sessions.append(None)

                for session in slot_events_for_time:
                    if session.slot.room == room:

                        sessions[i] = {
                            'break_event': session.activity.break_event,
                            'title': session.activity.title,
                            'conference_event': session.activity.conference_event,
                            'name': session.activity.all_presenter_names,
                            'time': session.slot.time.strftime('%H:%M'),
                            'end_time': session.end_time,
                            'id': session.activity.proposal_id,
                            'ical_id': session.ical_id,
                            'rowspan': 1,
                            'colspan': 1,
                            'spanned': False,
                            'room': session.slot.room.name,
                            'track': session.activity.track,
                        }
            matrix.append(sessions)

        for i, time_ in enumerate(times_for_day):
            for j, session in enumerate(matrix[i]):
                if session is not None:
                    # See if it's a long session
                    session_rowspan = 1
                    for k, later_time in enumerate(times_for_day[i + 1:]):
                        if session['end_time'] > later_time:
                            session_rowspan += 1
                            matrix[i + k + 1][j] = copy(session)
                            matrix[i + k + 1][j]['spanned'] = True
                        else:
                            break
                    matrix[i][j]['rowspan'] = session_rowspan

                    # See if it's a wide session
                    colspan = 1
                    for k, later_session in enumerate(matrix[i][j + 1:]):
                        if session and later_session and session['name'] == later_session['name']:
                            colspan += 1
                            matrix[i][j + k + 1]['spanned'] = True
                        else:
                            break
                    matrix[i][j]['colspan'] = colspan

                    # Make the YAML more bearable
                    matrix[i][j]['end_time'] = matrix[i][j]['end_time'].strftime('%H:%M')

        times_for_day = [x.strftime('%H:%M') for x in times_for_day]

        all_sessions[day.strftime('%Y-%m-%d')] = {
            'times': times_for_day,
            'rooms': room_names_for_day,
            'matrix': matrix
        }

    try:
        Cache.objects.get(key='schedule').delete()
    except Cache.DoesNotExist:
        pass

    schedule_cache = Cache(key='schedule', value=json.dumps(all_sessions))
    schedule_cache.save()

    return all_sessions


def generate_ical(slot_events, token):
    london_time = timezone('Europe/London')
    cal = Calendar()
    cal['X-WR-CALNAME'] = vText('PyCon UK 2018')

    for slot_event in slot_events:
        if (not slot_event.activity.break_event or
                (slot_event.activity.break_event and slot_event.slot.room.name == 'Assembly Room')):

            event = Event()

            event.add('summary', slot_event.activity.title)
            event.add('dtstart', datetime.combine(slot_event.slot.date, slot_event.slot.time, tzinfo=london_time))
            event.add('duration', slot_event.slot.duration)
            event.add('dtstamp', datetime.now())

            if slot_event.activity.break_event:
                event.add('uid', f'{slot_event.ical_id}-{slot_event.slot.time.hour}')
            else:
                event.add('uid', f'{slot_event.ical_id}')
                event.add('location', slot_event.slot.room.name)

            if not slot_event.activity.conference_event:
                event.add('description', slot_event.activity.description)
                for speaker in slot_event.activity.all_presenter_names.split(', '):
                    attendee = vCalAddress(f'http://example.com/{slugify(speaker)}')
                    attendee.params['cn'] = vText(speaker)
                    attendee.params['role'] = vText('REQ-PARTICIPANT')
                    event.add('attendee', attendee, encode=0)

            cal.add_component(event)

    try:
        Cache.objects.get(key=token).delete()
    except Cache.DoesNotExist:
        pass

    ical = cal.to_ical().decode('utf-8')

    ical_cache = Cache(key=token, value=ical)
    ical_cache.save()

    return ical
