from django.urls import path

import ironcage.views


urlpatterns = [
    path('', ironcage.views.index, name='index'),
    path('500/', ironcage.views.error, name='error'),
    path('log/', ironcage.views.log, name='log'),
]
