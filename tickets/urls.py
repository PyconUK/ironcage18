from django.conf.urls import url

from . import views

app_name = 'tickets'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/educator/new/$', views.new_educator_order, name='new_educator_order'),
    url(r'^orders/(?P<order_id>\w+)/edit/$', views.order_edit, name='order_edit'),
    url(r'^tickets/(?P<ticket_id>\w+)/$', views.ticket, name='ticket'),
    url(r'^invitations/(?P<token>\w+)/$', views.ticket_invitation, name='ticket_invitation'),
    url(r'^free/new/$', views.new_free_ticket, name='new_free_ticket'),
    url(r'^ticket_info/(?P<ticket_id>\w+)/$', views.ticket_info, name='ticket_info'),
]
