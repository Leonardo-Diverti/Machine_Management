from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'machines', views.MachineViewSet, basename='machine')

urlpatterns = [
    path('', include(router.urls)),
    # Dati IT per macchinario
    path('machines/<int:machine_id>/it-data/',
         views.MachineITDataView.as_view(), name='machine-it-data'),
    # Dati tecnici per macchinario
    path('machines/<int:machine_id>/tech-data/',
         views.MachineTechDataView.as_view(), name='machine-tech-data'),
    # Documenti tecnici per macchinario
    path('machines/<int:machine_id>/documents/',
         views.MachineDocumentViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='machine-documents'),
    path('machines/<int:machine_id>/documents/<int:pk>/',
         views.MachineDocumentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
         name='machine-document-detail'),
    # Documenti amministrativi per macchinario
    path('machines/<int:machine_id>/admin-documents/',
         views.MachineAdminDocumentViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='machine-admin-documents'),
    path('machines/<int:machine_id>/admin-documents/<int:pk>/',
         views.MachineAdminDocumentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
         name='machine-admin-document-detail'),
]
