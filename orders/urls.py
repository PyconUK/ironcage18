from django.conf.urls import url

from tickets import views

app_name = 'orders'

urlpatterns = [
    url(r'^(?P<order_id>\w+)/$', views.order, name='order'),
    url(r'^(?P<order_id>\w+)/payment/$', views.order_payment, name='order_payment'),
    url(r'^(?P<order_id>\w+)/receipt/$', views.order_receipt, name='order_receipt'),
    url(r'^(?P<order_id>\w+)/credit-note/(?P<refund_id>\w+)/$', views.refund_credit_note, name='refund_credit_note'),
]
