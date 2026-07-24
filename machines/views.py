# Questo file implementa le view per la gestione dei macchinari e dei relativi dati.
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction

from accounts.permissions import (
    HasFieldPermission,
    get_user_field_permissions,
    can_write_field,
    can_access_document_model,
    can_update_checklist_item,
    get_user_office_code,
)
from .models import (Machine, MachineITData, MachineTechData,
                     MachineDocument, MachineAdminDocument, MachineStatusLog,
                     MachineChecklistItem)
from .serializers import (MachineListSerializer, MachineDetailSerializer,
                          MachineITDataSerializer, MachineTechDataSerializer,
                          MachineDocumentSerializer, MachineAdminDocumentSerializer,
                          MachineStatusLogSerializer, MachineChecklistItemSerializer)
from .filters import MachineFilter
from .checklists import create_checklist_for_machine
from django.utils import timezone

class MachineViewSet(viewsets.ModelViewSet):
    """ViewSet per macchinari con RBAC"""
    queryset = Machine.objects.all().select_related('it_data', 'tech_data').prefetch_related(
        'checklist_items'
    )
    permission_classes = [IsAuthenticated, HasFieldPermission]
    filterset_class = MachineFilter
    search_fields = ['cdl', 'cc', 'capannone']
    ordering_fields = ['cdl', 'cc', 'capannone', 'anno_avviamento', 'stato', 'updated_at']

    def create(self, request, *args, **kwargs):
        """Blocca la creazione se l'utente non è dell'Ufficio Tecnico o Superuser"""
        if not request.user.is_superuser:
            if get_user_office_code(request.user) != 'TECH':
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Solo l'Ufficio Tecnico può creare nuovi macchinari.")
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Consente la cancellazione solo all'Ufficio Tecnico o ai superuser."""
        if not request.user.is_superuser and get_user_office_code(request.user) != 'TECH':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Solo l'Ufficio Tecnico può eliminare i macchinari."
            )
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == 'list':
            return MachineListSerializer
        return MachineDetailSerializer

    def perform_create(self, serializer):
        machine = serializer.save(stato='in_costruzione')
        # Crea automaticamente i record dei dati IT e tecnici
        MachineITData.objects.get_or_create(machine=machine)
        MachineTechData.objects.get_or_create(machine=machine)
        create_checklist_for_machine(machine)

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

    @action(detail=True, methods=['get'])
    def checklist(self, request, pk=None):
        """Restituisce le attivita' di avviamento della macchina."""
        machine = self.get_object()
        items = machine.checklist_items.prefetch_related('documents').all()
        return Response(MachineChecklistItemSerializer(items, many=True).data)

    @action(detail=True, methods=['patch'], url_path=r'checklist/(?P<item_id>[0-9]+)')
    @transaction.atomic
    def update_checklist_item(self, request, pk=None, item_id=None):
        """Aggiorna una voce checklist rispettando l'ufficio dell'utente."""
        machine = self.get_object()
        item = get_object_or_404(MachineChecklistItem, pk=item_id, machine=machine)
        if machine.stato != 'in_costruzione':
            return Response(
                {'error': "La checklist e' modificabile solo durante la costruzione."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not can_update_checklist_item(request.user, item):
            return Response(
                {'error': "Non hai i permessi per modificare questa attivita'."},
                status=status.HTTP_403_FORBIDDEN
            )
        if 'completata' not in request.data:
            return Response({'error': 'Il campo completata è obbligatorio.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if bool(request.data['completata']) and item.document_types:
            uploaded_types = set(item.documents.values_list('tipo_documento', flat=True))
            missing_types = [
                document_type for document_type in item.document_types
                if document_type not in uploaded_types
            ]
            if missing_types:
                document_labels = dict(MachineDocument.TIPO_CHOICES)
                missing_labels = [
                    document_labels.get(document_type, document_type)
                    for document_type in missing_types
                ]
                return Response({
                    'error': (
                        f'La fase "{item.descrizione}" non può essere completata: '
                        f'mancano i documenti richiesti ({", ".join(missing_labels)}).'
                    ),
                    'missing_documents': [
                        {'tipo_documento': document_type, 'label': label}
                        for document_type, label in zip(missing_types, missing_labels)
                    ],
                }, status=status.HTTP_400_BAD_REQUEST)

        is_last_incomplete_item = item.completata is False and not machine.checklist_items.filter(
            completata=False
        ).exclude(pk=item.pk).exists()
        if bool(request.data['completata']) and is_last_incomplete_item:
            missing_documents = []
            for checklist_item in machine.checklist_items.prefetch_related('documents'):
                uploaded_types = set(
                    checklist_item.documents.values_list('tipo_documento', flat=True)
                )
                for document_type in checklist_item.document_types:
                    if document_type not in uploaded_types:
                        missing_documents.append({
                            'fase': checklist_item.descrizione,
                            'tipo_documento': document_type,
                        })

            if missing_documents:
                return Response({
                    'error': 'La macchina non può entrare in produzione: mancano documenti richiesti.',
                    'missing_documents': missing_documents,
                }, status=status.HTTP_400_BAD_REQUEST)

        item.completata = bool(request.data['completata'])
        item.completata_at = timezone.now() if item.completata else None
        item.completata_da = request.user if item.completata else None
        item.save(update_fields=['completata', 'completata_at', 'completata_da'])

        if item.completata and is_last_incomplete_item:
            machine.stato = 'attiva'
            machine.save(update_fields=['stato', 'updated_at'])
            latest_log = machine.status_logs.first()
            MachineStatusLog.objects.create(
                machine=machine,
                stato='attiva',
                pezzi_buoni=latest_log.pezzi_buoni if latest_log else 0,
                fermi_macchina=latest_log.fermi_macchina if latest_log else 0,
            )

        return Response(MachineChecklistItemSerializer(item).data)

    @action(detail=False, methods=['get'])
    def live_status(self, request):
        """Stato live di tutti i macchinari (per dashboard real-time)"""
        machines = Machine.objects.filter(stato__in=['attiva', 'in_manutenzione', 'ferma'])
        result = []
        for machine in machines:
            latest_log = machine.status_logs.first()
            data = {
                'id': machine.id,
                'cdl': machine.cdl,
                'cc': machine.cc,
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
    def locations(self, request):
        """Restituisce tutte le localita' gia' presenti nell'anagrafica."""
        locations = Machine.objects.exclude(capannone__isnull=True).exclude(
            capannone=''
        ).values_list('capannone', flat=True).distinct().order_by('capannone')
        return Response(list(locations))

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

    def _ensure_access(self, action):
        user = self.request.user
        if not can_access_document_model(user, 'MachineDocument', action):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per accedere ai documenti tecnici.')

    def get_queryset(self):
        self._ensure_access('read')
        machine_id = self.kwargs.get('machine_id')
        if machine_id:
            return MachineDocument.objects.filter(machine_id=machine_id)
        return MachineDocument.objects.all()

    def perform_create(self, serializer):
        self._ensure_access('write')
        user = self.request.user
        machine_id = self.kwargs.get('machine_id')
        machine = get_object_or_404(Machine, pk=machine_id)
        checklist_item_id = self.request.data.get('checklist_item_id')
        checklist_item = None
        if checklist_item_id:
            checklist_item = get_object_or_404(
                MachineChecklistItem, pk=checklist_item_id, machine=machine
            )
            document_type = self.request.data.get('tipo_documento')
            if document_type not in checklist_item.document_types:
                from rest_framework.exceptions import ValidationError
                required = ', '.join(
                    dict(MachineDocument.TIPO_CHOICES).get(value, value)
                    for value in checklist_item.document_types
                )
                raise ValidationError({
                    'tipo_documento': (
                        f'Il documento non è valido per la fase "{checklist_item.descrizione}". '
                        f'Tipi richiesti: {required or "nessuno"}.'
                    )
                })
        document = serializer.save(
            machine=machine,
            uploaded_by=user,
            nome_file=self.request.FILES.get('file', '').name if self.request.FILES.get('file') else ''
        )
        if checklist_item:
            document.checklist_items.add(checklist_item)

    def perform_destroy(self, instance):
        self._ensure_access('write')
        instance.delete()


class MachineAdminDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet per i documenti amministrativi"""
    serializer_class = MachineAdminDocumentSerializer
    permission_classes = [IsAuthenticated, HasFieldPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _ensure_access(self, action):
        user = self.request.user
        if not can_access_document_model(user, 'MachineAdminDocument', action):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per accedere ai documenti amministrativi.')

    def get_queryset(self):
        self._ensure_access('read')
        machine_id = self.kwargs.get('machine_id')
        if machine_id:
            return MachineAdminDocument.objects.filter(machine_id=machine_id)
        return MachineAdminDocument.objects.all()

    def perform_create(self, serializer):
        self._ensure_access('write')
        user = self.request.user
        machine_id = self.kwargs.get('machine_id')
        machine = get_object_or_404(Machine, pk=machine_id)
        serializer.save(machine=machine, uploaded_by=user)

    def perform_destroy(self, instance):
        self._ensure_access('write')
        instance.delete()
