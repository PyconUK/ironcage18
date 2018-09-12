from django.conf.urls import url

from . import views

app_name = 'schedule'

urlpatterns = [
    url(r'^$', views.schedule, name='schedule'),
    url(r'^upload/$', views.upload_schedule, name='schedule_upload'),
    url(r'^timetable/upload/$', views.upload_timetable, name='timetable_upload'),
    url(r'^interest/$', views.interest, name='interest'),
    url(r'^ical/(?P<token>\w+)/$', views.ical, name='ical'),
    url(r'^yaml/$', views.import_timetable, name='yaml'),
    url(r'^item/(?P<proposal_id>[\w\d]{4})/$', views.view_proposal, name='view_proposal'),
    url(r'^json/$', views.schedule_json, name='schedule_json'),
]
