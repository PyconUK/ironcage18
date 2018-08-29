from django.conf.urls import url

from . import views

app_name = 'extras'

urlpatterns = [
    url(r'^children/orders/new/$', views.new_children_order, name='new_children_order'),
    url(r'^children/orders/(?P<order_id>\w+)/edit/$', views.children_order_edit, name='children_order_edit'),
    url(r'^children/tickets/$', views.children_ticket, name='children_ticket'),
    url(r'^dinner/orders/new/(?P<location_id>\w+)$', views.new_dinner_order, name='new_dinner_order'),
    url(r'^dinner/orders/(?P<order_id>\w+)/edit/$', views.dinner_order_edit, name='dinner_order_edit'),
    url(r'^dinner/tickets/$', views.dinner_ticket, name='dinner_ticket'),
    url(r'^dinner/tickets/(?P<item_id>\w+)/edit/$', views.dinner_ticket_edit, name='dinner_ticket_edit'),
]
