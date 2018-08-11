import codecs
import csv
from datetime import time, timedelta
from math import floor

import yaml
from django.contrib import messages

from cfp.models import Proposal
from schedule.models import Room, Slot, SlotEvent


def get_time(seconds):
    hour = floor(seconds / (60 * 60))
    minute = int((seconds - (hour * 60 * 60)) / 60)

    return time(hour=hour, minute=minute)


def import_schedule(f, request):
    SlotEvent.objects.all().delete()

    reader = csv.reader(codecs.iterdecode(f, 'utf-8'))
    for i, (event_index, event, slot_index, slot) in enumerate(reader):
        if i == 0:
            continue
        date, time, *room = slot.split(' ')
        room = ' '.join(room)

        try:
            activity = Proposal.objects.get(title=event)
        except Proposal.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Couldn't find {event}")
            continue

        room = Room.objects.get(name=room)

        try:
            slot = Slot.objects.get(room=room, date=date, time=time)
            SlotEvent.objects.get_or_create(
                activity=activity,
                slot=slot
            )
        except Slot.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Couldn't find {room} on {date} at {time}")


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
