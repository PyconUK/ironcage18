from django.urls import include, path

import accounts.views
import ironcage.views


urlpatterns = [
    path('', ironcage.views.index, name='index'),
    path('accounts/register/', accounts.views.register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('orders/', include('orders.urls')),
    path('profile/', include('accounts.urls')),
    path('reports/', include('reports.urls')),
    path('tickets/', include('tickets.urls')),
    path('500/', ironcage.views.error, name='error'),
    path('log/', ironcage.views.log, name='log'),
]
