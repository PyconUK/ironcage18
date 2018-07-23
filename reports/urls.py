from django.conf.urls import url

from . import reports, views

app_name = 'reports'

urlpatterns = [
    url(report.path(), report.as_view(), name=report.url_name())
    for report in reports.reports
]

urlpatterns.extend([
    url(r'^accounts/users/(?P<user_id>\w+)/$', views.accounts_user, name='accounts_user'),
    url(r'^tickets/orders/(?P<order_id>\w+)/$', views.tickets_order, name='tickets_order'),
    url(r'^tickets/tickets/(?P<ticket_id>\w+)/$', views.tickets_ticket, name='tickets_ticket'),
    url(r'^finaid/$', views.finaid_report, name='finaid_report'),
    url('^$', views.index, name='index'),
])
