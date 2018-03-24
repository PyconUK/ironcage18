from django.urls import path

import ironcage.views


urlpatterns = [
    path('500/', ironcage.views.error, name='error'),
    path('log/', ironcage.views.log, name='log'),
]
