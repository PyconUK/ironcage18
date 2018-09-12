import json

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import render

from accounts.models import User
from cfp.models import Proposal
from schedule.models import Cache, SlotEvent

from .actions import (generate_ical, generate_schedule_page_data,
                      import_schedule, import_timetable)
from .forms import UploadScheduleForm, UploadTimetableForm


def schedule(request):

    try:
        schedule_cache = Cache.objects.get(key='schedule')
        all_sessions = json.loads(schedule_cache.value)
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


def schedule_json(request):
    try:
        schedule_cache = Cache.objects.get(key='schedule')
        all_sessions = json.loads(schedule_cache.value)
    except Cache.DoesNotExist:
        all_sessions = generate_schedule_page_data()

    return JsonResponse(all_sessions)


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


@login_required
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
    try:
        Cache.objects.get(key=request.user.ical_token).delete()
    except Cache.DoesNotExist:
        pass

    return HttpResponse()


def ical(request, token):
    try:
        ical = Cache.objects.get(key=token).value
    except Cache.DoesNotExist:
        if token == 'full':
            slots = SlotEvent.objects.all()
        else:
            try:
                user = User.objects.get(ical_token=token)
                if len(user.items_of_interest) == 0:
                    slots = SlotEvent.objects.all()
                else:
                    slots = SlotEvent.objects.filter(
                        Q(ical_id__in=user.items_of_interest) | Q(activity__break_event=True)
                    )
            except User.DoesNotExist:
                return Http404

        ical = generate_ical(slots, token)

    return HttpResponse(ical, content_type="text/calendar")


def view_proposal(request, proposal_id):
    proposal = Proposal.objects.get_by_proposal_id_or_404(proposal_id)
    slots = SlotEvent.objects.filter(activity=proposal).all()

    context = {
        'proposal': proposal,
        'slots': slots,
    }
    return render(request, 'schedule/view_proposal.html', context)
