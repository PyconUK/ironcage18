import csv

from datetime import datetime, timezone, date, timedelta

from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render

from .models import Session, Room, Stream

from copy import copy


def schedule(request):

    days = [date(2018, 9, 15), date(2018, 9, 16), date(2018, 9, 17), date(2018, 9, 18), date(2018, 9, 19)]

    all_sessions = {}

    for day in days:

        streams_for_day = Stream.objects.filter(
            day=day, visible=True
        ).order_by('room__order', 'room__name').all()

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
                'stream__room__order',
                'stream__room__name'
            ).all()

            sessions = []

            for i, stream in enumerate(streams_for_day):
                sessions.append(None)
                for session in sessions_for_time:
                    if session.stream == stream:

                        # Temporary
                        if session.activity.session_type == 'talk':
                            length = timedelta(minutes=30)
                        elif session.activity.session_type == 'workshop':
                            length = timedelta(minutes=120)
                        else:
                            length = timedelta(minutes=60)
                        # End Temporary

                        sessions[i] = {
                            'break_event': session.activity.break_event,
                            'title': session.activity.title,
                            'conference_event': session.activity.conference_event,
                            'name': session.activity.proposer.name,
                            'length': length,
                            'time': session.time,
                            'end_time': (datetime.combine(date(2018, 1, 1), session.time) + length).time(),
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
