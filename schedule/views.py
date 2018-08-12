import yaml
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from schedule.models import Cache

from .actions import (generate_schedule_page_data, import_schedule,
                      import_timetable)
from .forms import UploadScheduleForm, UploadTimetableForm


@staff_member_required(login_url='login')
def schedule(request):

    try:
        schedule_cache = Cache.objects.get(key='schedule')
        all_sessions = yaml.load(schedule_cache.value)
    except Cache.DoesNotExist:
        all_sessions = generate_schedule_page_data()

    users_sessions = []
    if not request.user.is_anonymous:
        users_sessions = request.user.items_of_interest

    context = {
        'sessions': all_sessions,
        'users_sessions': users_sessions,
        'anonymous_user': request.user.is_anonymous,
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


def interest(request):
    if request.method == 'POST':
        proposal_id = request.GET['id']
        if proposal_id not in request.user.items_of_interest:
            request.user.items_of_interest.append(proposal_id)
    elif request.method == 'DELETE':
        proposal_id = request.GET['id']
        if proposal_id in request.user.items_of_interest:
            request.user.items_of_interest.remove(proposal_id)

    request.user.save()

    return HttpResponse()
