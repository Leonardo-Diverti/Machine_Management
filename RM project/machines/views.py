# Questo file implementa le view per la gestione dei macchinari e dei relativi dati.
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from accounts.permissions import HasFieldPermission, get_user_field_permissions, can_write_field

from .models import (Machine, MachineITData, MachineTechData,
                     MachineDocument, MachineAdminDocument, MachineStatusLog)
from .serializers import (MachineListSerializer, MachineDetailSerializer,
                          MachineITDataSerializer, MachineTechDataSerializer,
                          MachineDocumentSerializer, MachineAdminDocumentSerializer,
                          MachineStatusLogSerializer)
from .filters import MachineFilter


class MachineViewSet(viewsets.ModelViewSet):
    """ViewSet per macchinari con RBAC"""
    queryset = Machine.objects.all().select_related('it_data', 'tech_data')
    permission_classes = [IsAuthenticated, HasFieldPermission]
    filterset_class = MachineFilter
    search_fields = ['matricola', 'capannone']
    ordering_fields = ['matricola', 'capannone', 'anno_avviamento', 'stato', 'updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return MachineListSerializer
        return MachineDetailSerializer

    def perform_create(self, serializer):
        machine = serializer.save()
        # Crea automaticamente i record dei dati IT e tecnici
        MachineITData.objects.get_or_create(machine=machine)
        MachineTechData.objects.get_or_create(machine=machine)

    def update(self, request, *args, **kwargs):
        """Override per validare i permessi di scrittura sui campi"""
        machine = self.get_object()
        user = request.user

        if not user.is_superuser:
            perms = get_user_field_permissions(user, 'Machine')
            for field in request.data:
                if field in ['id', 'created_at', 'updated_at']:
                    continue
                if not can_write_field(user, 'Machine', field):
                    return Response(
                        {'error': f'Non hai i permessi per modificare il campo "{field}".'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Override per PATCH con validazione RBAC"""
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def status_logs(self, request, pk=None):
        """Ultimi log di stato per un macchinario"""
        machine = self.get_object()
        logs = machine.status_logs.all()[:50]
        serializer = MachineStatusLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def live_status(self, request):
        """Stato live di tutti i macchinari (per dashboard real-time)"""
        machines = Machine.objects.filter(stato__in=['attiva', 'in_manutenzione', 'ferma'])
        result = []
        for machine in machines:
            latest_log = machine.status_logs.first()
            data = {
                'id': machine.id,
                'matricola': machine.matricola,
                'capannone': machine.capannone,
                'stato': machine.stato,
                'pezzi_buoni': latest_log.pezzi_buoni if latest_log else 0,
                'fermi_macchina': latest_log.fermi_macchina if latest_log else 0,
                'orario_fermo': latest_log.orario_fermo if latest_log else None,
                'motivo_fermo': latest_log.motivo_fermo if latest_log else None,
                'last_update': latest_log.timestamp if latest_log else None,
            }
            result.append(data)
        return Response(result)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiche generali macchinari"""
        total = Machine.objects.count()
        attive = Machine.objects.filter(stato='attiva').count()
        ferme = Machine.objects.filter(stato='ferma').count()
        manutenzione = Machine.objects.filter(stato='in_manutenzione').count()
        dismesse = Machine.objects.filter(stato='dismessa').count()
        return Response({
            'totale': total,
            'attive': attive,
            'ferme': ferme,
            'in_manutenzione': manutenzione,
            'dismesse': dismesse,
        })


class MachineITDataView(generics.RetrieveUpdateAPIView):
    """View per aggiornare i dati IT di un macchinario"""
    serializer_class = MachineITDataSerializer
    permission_classes = [IsAuthenticated, HasFieldPermission]

    def get_object(self):
        machine_id = self.kwargs['machine_id']
        machine = get_object_or_404(Machine, pk=machine_id)
        obj, _ = MachineITData.objects.get_or_create(machine=machine)
        return obj

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            for field in self.request.data:
                if field in ['id', 'machine', 'updated_at', 'updated_by']:
                    continue
                if not can_write_field(user, 'MachineITData', field):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied(
                        f'Non hai i permessi per modificare il campo "{field}".'
                    )
        serializer.save(updated_by=user)


class MachineTechDataView(generics.RetrieveUpdateAPIView):
    """View per aggiornare i dati tecnici di un macchinario"""
    serializer_class = MachineTechDataSerializer
    permission_classes = [IsAuthenticated, HasFieldPermission]

    def get_object(self):
        machine_id = self.kwargs['machine_id']
        machine = get_object_or_404(Machine, pk=machine_id)
        obj, _ = MachineTechData.objects.get_or_create(machine=machine)
        return obj

    def perform_update(self, serializer):
        user = self.request.user
        if not user.is_superuser:
            for field in self.request.data:
                if field in ['id', 'machine', 'updated_at', 'updated_by']:
                    continue
                if not can_write_field(user, 'MachineTechData', field):
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied(
                        f'Non hai i permessi per modificare il campo "{field}".'
                    )
        serializer.save(updated_by=user)


class MachineDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet per i documenti tecnici"""
    serializer_class = MachineDocumentSerializer
    permission_classes = [IsAuthenticated, HasFieldPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        machine_id = self.kwargs.get('machine_id')
        if machine_id:
            return MachineDocument.objects.filter(machine_id=machine_id)
        return MachineDocument.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser and not can_write_field(user, 'MachineDocument', '*'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per caricare documenti tecnici.')
        machine_id = self.kwargs.get('machine_id')
        machine = get_object_or_404(Machine, pk=machine_id)
        serializer.save(
            machine=machine,
            uploaded_by=user,
            nome_file=self.request.FILES.get('file', '').name if self.request.FILES.get('file') else ''
        )


class MachineAdminDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet per i documenti amministrativi"""
    serializer_class = MachineAdminDocumentSerializer
    permission_classes = [IsAuthenticated, HasFieldPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        machine_id = self.kwargs.get('machine_id')
        if machine_id:
            return MachineAdminDocument.objects.filter(machine_id=machine_id)
        return MachineAdminDocument.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_superuser and not can_write_field(user, 'MachineAdminDocument', '*'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per caricare documenti amministrativi.')
        machine_id = self.kwargs.get('machine_id')
        machine = get_object_or_404(Machine, pk=machine_id)
        serializer.save(machine=machine, uploaded_by=user)
