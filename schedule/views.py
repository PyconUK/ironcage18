from copy import copy
from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render

from schedule.models import Slot, SlotEvent

from .actions import import_schedule, import_timetable
from .forms import UploadScheduleForm, UploadTimetableForm


@staff_member_required(login_url='login')
def schedule(request):

    days = [date(2018, 9, 15), date(2018, 9, 16), date(2018, 9, 17), date(2018, 9, 18), date(2018, 9, 19)]

    all_sessions = {}

    for day in days:

        slots_for_day = Slot.objects.filter(
            date=day, visible=True
        ).order_by('room__name').all()

        rooms_for_day_query = Slot.objects.filter(
            date=day
        ).distinct(
            'room'
        )

        rooms_for_day = [x.room for x in rooms_for_day_query]

        times_for_day_query = Slot.objects.filter(
            date=day
        ).distinct(
            'time'
        ).values(
            'time'
        )
        times_for_day = [x['time'] for x in times_for_day_query]

        all_sessions[day] = {
            'times': times_for_day,
            'slots': slots_for_day,
            'rooms': rooms_for_day,
        }

        # lists of sessions, one list per time
        matrix = []

        # Make blank matrix
        for time in times_for_day:
            slot_events_for_time = SlotEvent.objects.filter(
                slot__date=day,
                slot__time=time
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
                            'length': session.slot.duration,
                            'time': session.slot.time,
                            'end_time': session.end_time,
                            'id': session.activity.proposal_id,
                            'rowspan': 1,
                            'colspan': 1,
                            'spanned': False,
                            'room': session.slot.room.name,
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
            'rooms': rooms_for_day,
            'slots': slots_for_day,
            'matrix': matrix
        }

    context = {
        'sessions': all_sessions,
        'wide': True,
        'js_paths': ['schedule/schedule.js'],
    }
    return render(request, 'schedule/schedule.html', context)


@staff_member_required(login_url='login')
def upload_schedule(request):
    if request.method == 'POST':
        form = UploadScheduleForm(request.POST, request.FILES)
        if form.is_valid():
            import_schedule(request.FILES['schedule'], request)
            return HttpResponseRedirect('/schedule/')
    else:
        form = UploadScheduleForm()
    return render(request, 'schedule/upload_schedule.html', {'form': form})


@staff_member_required(login_url='login')
def upload_timetable(request):
    if request.method == 'POST':
        form = UploadTimetableForm(request.POST, request.FILES)
        if form.is_valid():
            import_timetable(request.FILES['timetable'], request.FILES['unbounded'], request)
            return HttpResponseRedirect('/schedule/upload/')
    else:
        form = UploadTimetableForm()
    return render(request, 'schedule/upload_timetable.html', {'form': form})
