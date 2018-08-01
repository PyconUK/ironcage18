import csv
import codecs
from copy import copy
from datetime import date

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render

from cfp.models import Proposal
from schedule.models import Room, Session, Stream

from .forms import UploadFileForm


@staff_member_required(login_url='login')
def schedule(request):

    days = [date(2018, 9, 15), date(2018, 9, 16), date(2018, 9, 17), date(2018, 9, 18), date(2018, 9, 19)]

    all_sessions = {}

    for day in days:

        streams_for_day = Stream.objects.filter(
            day=day, visible=True
        ).order_by('order', 'room__name').all()

        sessions_for_day = Session.objects.filter(
            stream__in=streams_for_day
        ).all()

        times_for_day_query = Session.objects.filter(
            stream__day=day
        ).distinct(
            'time'
        ).values(
            'time'
        )
        times_for_day = [x['time'] for x in times_for_day_query]

        all_sessions[day] = {
            'times': times_for_day,
            'streams': streams_for_day,
            'sessions': sessions_for_day,
        }

        # lists of sessions, one list per time
        matrix = []

        # Make blank matrix
        for time in times_for_day:
            sessions_for_time = Session.objects.filter(
                stream__day=day,
                time=time,
            ).order_by(
                'stream__order',
                'stream__room__name'
            ).all()

            sessions = []

            for i, stream in enumerate(streams_for_day):
                sessions.append(None)
                for session in sessions_for_time:
                    if session.stream == stream:

                        sessions[i] = {
                            'break_event': session.activity.break_event,
                            'title': session.activity.title,
                            'conference_event': session.activity.conference_event,
                            'name': session.activity.proposer.name,
                            'length': session.activity.length,
                            'time': session.time,
                            'end_time': session.end_time,
                            'rowspan': 1,
                            'colspan': 1,
                            'spanned': False,
                            'room': session.stream.room.name,
                        }
            matrix.append(sessions)

        for i, time in enumerate(times_for_day):
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

        all_sessions[day] = {
            'times': times_for_day,
            'streams': streams_for_day,
            'sessions': sessions_for_day,
            'matrix': matrix
        }

    context = {
        'sessions': all_sessions,
        'wide': True
    }
    return render(request, 'schedule/schedule.html', context)


def import_schedule(f, request):
    Session.objects.all().delete()

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
            stream = Stream.objects.get(room=room, day=date, stream_type='day')
        except Stream.DoesNotExist:
            messages.add_message(request, messages.ERROR, f"Couldn't find {room} on {date}")

        Session.objects.get_or_create(
            activity=activity,
            stream=stream,
            time=time,
            length=activity.length
        )


@staff_member_required(login_url='login')
def upload_schedule(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            import_schedule(request.FILES['file'], request)
            return HttpResponseRedirect('/schedule/')
    else:
        form = UploadFileForm()
    return render(request, 'schedule/upload.html', {'form': form})
