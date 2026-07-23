from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MachineViewSet

router = DefaultRouter()
# Usiamo 'machines' invece di 'macchine' per far combaciare l'URL richiesto dal frontend (/api/machines/stats/)
router.register(r'machines', MachineViewSet, basename='machine')

urlpatterns = [
    path('', include(router.urls)),
]