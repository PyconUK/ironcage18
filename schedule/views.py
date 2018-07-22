import csv

from datetime import datetime, timezone, date, timedelta

from django_slack import slack_message

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render

from .models import Session, Room, Stream


def schedule(request):

    days = [date(2018, 9, 15), date(2018, 9, 16), date(2018, 9, 17), date(2018, 9, 18), date(2018, 9, 19)]

    all_sessions = {}

    for day in days:

        streams_for_day = Stream.objects.filter(day=day).order_by('room__order', 'room__name').all()

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
                        sessions[i] = session

            matrix.append(sessions)

        all_sessions[day] = {
            'times': times_for_day,
            'streams': streams_for_day,
            'sessions': sessions_for_day,
            'matrix': matrix
        }

        # # Fill in sessions
        # for time in times_for_day:
        #     for session in sessions_for_day:
        #         if session.



        # for session in sessions_for_day:
        #     all_sessions[day]['matrix'][session.time][session.stream] =
        #     # Temporary
        #     if session.activity.session_type == 'talk':
        #         length = timedelta(minutes=30)
        #     elif session.activity.session_type == 'workshop':
        #         length = timedelta(minutes=120)
        #     else:
        #         length = timedelta(minutes=60)
        #     # End Temporary

        #     if session.activity.all_rooms_event:
        #         for stream in streams_for_day:
        #             if all_sessions[day]['matrix'][session.time][stream] is None:
        #                 all_sessions[day]['matrix'][session.time][stream] = all_sessions[day]['matrix'][session.time][session.stream]

        #     # See if it's a long session
        #     session_end_time = (datetime.combine(date(2018, 1, 1), session.time) + length).time()
        #     session_gaps = 1
        #     for time in times_for_day[times_for_day.index(session.time) + 1:]:
        #         if session_end_time > time:
        #             session_gaps += 1
        #             all_sessions[day]['matrix'][time][session.stream] = {'long_session': True}

        #     all_sessions[day]['matrix'][session.time][session.stream]['rows'] = session_gaps

        # for time in all_sessions[day]['matrix']:
        #     for session in all_sessions[day]['matrix'][time]:
        #         if all_sessions[day]['matrix'][time][session] \
        #                 and all_sessions[day]['matrix'][time][session].get('all_rooms_event'):

        #             stream_keys = list(all_sessions[day]['matrix'][time].keys())
        #             remaining_session_keys = stream_keys[stream_keys.index(session) + 1:]
        #             for session_key in remaining_session_keys:

        #                 if all_sessions[day]['matrix'][time][session_key] == all_sessions[day]['matrix'][time][session]:
        #                     all_sessions[day]['matrix'][time][session]['cols'] += 1
        #                     all_sessions[day]['matrix'][time][session_key] = None
        #                 else:
        #                     break

        # print(all_sessions[day]['matrix'])


        # Look at a session
            # If session is all_rooms_event
                # If next session all_rooms_event
                    # next_session = None
                    # update_colspan
                # else
                    # continue



        # # Sort out the colspan for the all_rooms_events
        # for time in all_sessions[day]['matrix']:
        #     stream_keys = list[all_sessions[day]['matrix'][time].keys()]

        #     # print(stream_keys)

        #     for i, stream in enumerate(stream_keys):

        #         # print(i, stream)
        #         if (all_sessions[day]['matrix'][time][stream] is not None
        #                 and all_sessions[day]['matrix'][time][stream].get('all_rooms_event')):
        #             pass
        #             print(stream_keys[i])


        #             # print(all_sessions[day]['matrix'][time][stream])





            #  cols = 1
            #         print(sessions_keys.index(session))
            #             # if




        # print(all_sessionss)


    #     # print(sessions_by_stream_and_time_for_day)

    # #

    # #     for session in sessions_by_stream_and_time:
    # #         if all_sessions[day].get(session.stream.room) is None:
    # #             all_sessions[day][session.stream.room] = {}

    # #         all_sessions[day][session.stream.room][session.time] = {
    # #             'title': session.activity.title,
    # #             'name': session.activity.proposer.name,
    # #             'rows': 1
    # #         }

    # #         if session.activity.session_type == 'talk':
    # #             length = timedelta(minutes=30)
    # #         elif session.activity.session_type == 'workshop':
    # #             length = timedelta(minutes=120)
    # #         else:
    # #             length = timedelta(minutes=60)

    # #         session_end_time = (datetime.combine(date(2018, 1, 1), session.time) + length).time()
    # #         session_gaps = 1
    # #         for time in times[times.index(session.time) + 1:]:
    # #             if session_end_time > time:
    # #                 session_gaps += 1
    # #                 all_sessions[day][session.stream.room][time] = {'long_session': True}

    # #         all_sessions[day][session.stream.room][session.time]['rows'] = session_gaps


    # # # print(all_sessions)

    context = {
        # 'streams': streams_for_day,
        'sessions': all_sessions,
        # 'days': days,
        # 'times': times_for_day
    }
    return render(request, 'schedule/schedule.html', context)












# def schedule(request):

#     times = [x['time'] for x in Session.objects.distinct('time').values('time')]

#     days = ['2018-09-15', '2018-09-16', '2018-09-17', '2018-09-18', '2018-09-19']

#     all_sessions = {}

#     for day in days:
#         streams = Stream.objects.filter(day=day).all()
#         sessions_by_stream_and_time = Session.objects.filter(
#             stream__in=streams
#         ).order_by(
#             'stream', 'time'
#         ).all()

#         all_sessions[day] = {}

#         for session in sessions_by_stream_and_time:
#             if all_sessions[day].get(session.stream.room) is None:
#                 all_sessions[day][session.stream.room] = {}

#             all_sessions[day][session.stream.room][session.time] = {
#                 'title': session.activity.title,
#                 'name': session.activity.proposer.name,
#                 'rows': 1
#             }

#             if session.activity.session_type == 'talk':
#                 length = timedelta(minutes=30)
#             elif session.activity.session_type == 'workshop':
#                 length = timedelta(minutes=120)
#             else:
#                 length = timedelta(minutes=60)

#             session_end_time = (datetime.combine(date(2018, 1, 1), session.time) + length).time()
#             session_gaps = 1
#             for time in times[times.index(session.time) + 1:]:
#                 if session_end_time > time:
#                     session_gaps += 1
#                     all_sessions[day][session.stream.room][time] = {'long_session': True}

#             all_sessions[day][session.stream.room][session.time]['rows'] = session_gaps


#     # print(all_sessions)

#     context = {
#         'streams': streams,
#         'sessions': all_sessions,
#         'days': days,
#         'times': times
#     }
#     return render(request, 'schedule/schedule.html', context)
