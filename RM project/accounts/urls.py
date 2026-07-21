# Questo file definisce gli endpoint di autenticazione e profilo utente.
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('me/', views.me_view, name='me'),
    path('logout/', views.logout_view, name='logout'),
]
