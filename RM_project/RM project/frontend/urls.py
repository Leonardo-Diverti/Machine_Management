# Questo file definisce gli URL della parte frontend dell'applicazione.
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]
