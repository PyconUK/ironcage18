from django.conf.urls import url

from . import views

app_name = 'extras'

urlpatterns = [
    url(r'^orders/new/$', views.new_order, name='new_order'),
    url(r'^orders/(?P<order_id>\w+)/edit/$', views.order_edit, name='order_edit'),
]
