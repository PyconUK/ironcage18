from django.conf.urls import url

from . import views

app_name = 'botany'

urlpatterns = [
    url(r'^authorize/$', views.authorize)
]
