from django.conf.urls import url

from . import views

app_name = 'extras'

urlpatterns = [
    url(r'^children/orders/new/$', views.new_children_order, name='new_children_order'),
    url(r'^children/orders/(?P<order_id>\w+)/edit/$', views.children_order_edit, name='children_order_edit'),
    url(r'^children/tickets/$', views.children_ticket, name='children_ticket'),
]
