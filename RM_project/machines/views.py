# Questo file implementa le view per la gestione dei macchinari e dei relativi dati.
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.files.base import ContentFile

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
                     MachineChecklistItem, MachineFiscalBenefit,
                     MachineFiscalBenefitDocument, MachineFiscalBenefitMaintenanceYear,
                     MachineFiscalBenefitMaintenanceDocument)
from .serializers import (MachineListSerializer, MachineDetailSerializer,
                          MachineITDataSerializer, MachineTechDataSerializer,
                          MachineDocumentSerializer, MachineAdminDocumentSerializer,
                          MachineStatusLogSerializer, MachineChecklistItemSerializer,
                          MachineFiscalBenefitSerializer,
                          MachineFiscalBenefitDocumentSerializer,
                          MachineFiscalBenefitMaintenanceYearSerializer,
                          MachineFiscalBenefitMaintenanceDocumentSerializer)
from .filters import MachineFilter
from .checklists import create_checklist_for_machine
from django.utils import timezone


def build_safe_uploaded_file(uploaded_file):
    """Crea una copia in memoria del file caricato per evitare errori con i file temporanei."""
    if not uploaded_file:
        return None
    if hasattr(uploaded_file, 'read'):
        uploaded_file.open()
        content = uploaded_file.read()
        uploaded_file.seek(0)
        return ContentFile(content, name=getattr(uploaded_file, 'name', 'upload'))
    return uploaded_file


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
        machine = serializer.save(stato='inserimento_db')
        # Crea automaticamente i record dei dati IT e tecnici
        MachineITData.objects.get_or_create(machine=machine)
        MachineTechData.objects.get_or_create(machine=machine)
        create_checklist_for_machine(machine)

    def update(self, request, *args, **kwargs):
        """Override per validare i permessi di scrittura sui campi"""
        machine = self.get_object()
        user = request.user

        # Campi fiscali scrivibili solo dall'amministrazione
        fiscal_fields = {'id_investimento_rm', 'id_investimento_consulente', 'consulente'}
        # Campi interconnessione scrivibili solo dall'IT
        interconnessione_fields = {'interconnessione_stato', 'interconnessione_prevista',
                                    'data_interconnessione_prevista'}

        if not user.is_superuser:
            office_code = get_user_office_code(user)
            for field in request.data:
                if field in ['id', 'created_at', 'updated_at']:
                    continue
                if field in fiscal_fields:
                    if office_code != 'ADMIN':
                        return Response(
                            {'error': f'Solo l\'ufficio amministrazione può modificare "{field}".'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    try:
                        if not machine.benefit_fiscal.attivo:
                            return Response(
                                {'error': f'I campi fiscali possono essere inseriti solo per macchine con beneficio fiscale attivato.'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    except Exception:
                        return Response(
                            {'error': f'I campi fiscali possono essere inseriti solo per macchine con beneficio fiscale attivato.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    continue
                if field in interconnessione_fields:
                    if office_code != 'IT':
                        return Response(
                            {'error': f'Solo l\'ufficio IT può modificare "{field}".'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                    continue
                if not can_write_field(user, 'Machine', field):
                    return Response(
                        {'error': f'Non hai i permessi per modificare il campo "{field}".'},
                        status=status.HTTP_403_FORBIDDEN
                    )

        # Override dell'update originale
        response = super().update(request, *args, **kwargs)
        machine.refresh_from_db() # Refresh per assicurarsi che lo stato sia aggiornato
        


        return response

    def partial_update(self, request, *args, **kwargs):
        """Override per PATCH con validazione RBAC"""
        kwargs['partial'] = True
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
        # La checklist TECH è modificabile durante gli stati di avviamento.
        # La checklist IT è modificabile anche quando la macchina è in produzione.
        editable_states = ('inserimento_db', 'ordinata', 'in_costruzione')
        if item.ufficio == 'IT':
            editable_states += ('attiva', 'ferma', 'in_manutenzione')
            
        if machine.stato not in editable_states:
            msg = "La checklist tecnica è modificabile solo durante le fasi di avviamento."
            if item.ufficio == 'IT':
                msg = "La checklist IT non è modificabile in questo stato."
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)
        if not can_update_checklist_item(request.user, item):
            return Response(
                {'error': "Non hai i permessi per modificare questa attività."},
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

        # === Transizioni di stato basate su voci specifiche della checklist ===
        if item.completata:
            # Quando la voce 'ordini_macchina' viene completata → stato 'ordinata'
            if item.codice == 'ordini_macchina' and machine.stato == 'inserimento_db':
                machine.stato = 'ordinata'
                machine.save(update_fields=['stato', 'updated_at'])

            # Quando la voce 'entrata_merci' viene completata → stato 'in_costruzione'
            elif item.codice == 'entrata_merci' and machine.stato == 'ordinata':
                machine.stato = 'in_costruzione'
                machine.save(update_fields=['stato', 'updated_at'])

            # Quando la voce 'verbale_collaudo' viene completata → stato 'attiva'
            elif item.codice == 'verbale_collaudo' and machine.stato == 'in_costruzione':
                machine.stato = 'attiva'
                machine.save(update_fields=['stato', 'updated_at'])
                MachineStatusLog.objects.create(
                    machine=machine,
                    stato='attiva',
                )

            # Controlla se tutte le fasi IT sono completate → interconnessione diventa 'interconnessa'
            if item.ufficio == 'IT':
                it_items = machine.checklist_items.filter(ufficio='IT')
                if it_items.exists() and not it_items.filter(completata=False).exists():
                    tech_incomplete = machine.checklist_items.filter(ufficio='TECH', completata=False).exists()
                    if not tech_incomplete:
                        machine.interconnessione_stato = 'interconnessa'
                        machine.save(update_fields=['interconnessione_stato', 'updated_at'])
                        
            elif item.ufficio == 'TECH':
                tech_items = machine.checklist_items.filter(ufficio='TECH')
                if tech_items.exists() and not tech_items.filter(completata=False).exists():
                    it_items = machine.checklist_items.filter(ufficio='IT')
                    if it_items.exists() and not it_items.filter(completata=False).exists():
                        machine.interconnessione_stato = 'interconnessa'
                        machine.save(update_fields=['interconnessione_stato', 'updated_at'])

        # Se si de-completa una voce qualsiasi, verifica se l'interconnessione deve tornare indietro
        elif not item.completata:
            if machine.interconnessione_stato == 'interconnessa':
                if machine.interconnessione_prevista:
                    machine.interconnessione_stato = 'in_attesa'
                else:
                    machine.interconnessione_stato = 'non_interconnesso'
                machine.save(update_fields=['interconnessione_stato', 'updated_at'])

        return Response(MachineChecklistItemSerializer(item).data)

    @action(detail=True, methods=['get', 'post'])
    def benefit_fiscal(self, request, pk=None):
        """Gestione del beneficio fiscale per una macchina interconnessa."""
        machine = self.get_object()
        if get_user_office_code(request.user) not in {'ADMIN', 'TECH'} and not request.user.is_superuser:
            return Response({'error': 'Solo amministrazione o tecnico possono gestire il beneficio fiscale.'}, status=403)

        # Il beneficio fiscale è accessibile solo quando la macchina è interconnessa
        if machine.interconnessione_stato != 'interconnessa':
            return Response({'error': 'Il beneficio fiscale è disponibile solo per macchine interconnesse.'}, status=400)
            
        # Il beneficio fiscale è attivabile solo se l'accentratore è PLC
        try:
            if machine.it_data.tipo_accentratore != 'PLC':
                return Response({'error': 'Il beneficio fiscale è attivabile solo con accentratore PLC.'}, status=400)
        except getattr(machine, 'it_data').RelatedObjectDoesNotExist if hasattr(machine, 'it_data') else Exception:
            return Response({'error': 'Il beneficio fiscale è attivabile solo con accentratore PLC.'}, status=400)

        benefit, _ = MachineFiscalBenefit.objects.get_or_create(machine=machine)
        if request.method == 'GET':
            return Response(MachineFiscalBenefitSerializer(benefit).data)


        # Solo ADMIN può attivare il beneficio
        if get_user_office_code(request.user) != 'ADMIN' and not request.user.is_superuser:
            return Response({'error': 'Solo l\'ufficio amministrazione può attivare il beneficio fiscale.'}, status=403)

        attivo = request.data.get('attivo', False)
        if isinstance(attivo, str):
            attivo = attivo.lower() in {'true', '1', 'yes'}
        benefit.attivo = bool(attivo)
        if not benefit.attivo:
            benefit.chiuso = False
        benefit.save(update_fields=['attivo', 'chiuso', 'updated_at'])
        return Response(MachineFiscalBenefitSerializer(benefit).data)

    @action(detail=True, methods=['get', 'post'], url_path='interconnessione')
    def interconnessione(self, request, pk=None):
        """Gestione dell'interconnessione da parte dell'ufficio IT."""
        machine = self.get_object()

        if request.method == 'GET':
            return Response({
                'interconnessione_stato': machine.interconnessione_stato,
                'interconnessione_prevista': machine.interconnessione_prevista,
                'data_interconnessione_prevista': machine.data_interconnessione_prevista,
            })

        # Solo IT può modificare l'interconnessione
        if get_user_office_code(request.user) != 'IT' and not request.user.is_superuser:
            return Response({'error': 'Solo l\'ufficio IT può gestire l\'interconnessione.'}, status=403)

        prevista = request.data.get('interconnessione_prevista')
        if prevista is None:
            return Response({'error': 'Il campo interconnessione_prevista è obbligatorio.'}, status=400)

        if isinstance(prevista, str):
            prevista = prevista.lower() in {'true', '1', 'yes'}

        machine.interconnessione_prevista = bool(prevista)

        if machine.interconnessione_prevista:
            data_prevista = request.data.get('data_interconnessione_prevista')
            if not data_prevista:
                return Response({'error': 'La data di interconnessione prevista è obbligatoria quando l\'interconnessione è prevista.'}, status=400)
            machine.data_interconnessione_prevista = data_prevista
            # Se l'IT ha dichiarato che è prevista, il valore diventa 'in_attesa'
            # (a meno che tutte le fasi IT non siano già completate)
            it_items = machine.checklist_items.filter(ufficio='IT')
            tech_incomplete = machine.checklist_items.filter(ufficio='TECH', completata=False).exists()
            if it_items.exists() and not it_items.filter(completata=False).exists() and not tech_incomplete:
                machine.interconnessione_stato = 'interconnessa'
            else:
                machine.interconnessione_stato = 'in_attesa'
        else:
            machine.data_interconnessione_prevista = None
            # Se l'IT dichiara che non è prevista, torna a 'non_interconnesso'
            # (a meno che tutte le fasi IT non siano completate)
            it_items = machine.checklist_items.filter(ufficio='IT')
            tech_incomplete = machine.checklist_items.filter(ufficio='TECH', completata=False).exists()
            if it_items.exists() and not it_items.filter(completata=False).exists() and not tech_incomplete:
                machine.interconnessione_stato = 'interconnessa'
            else:
                machine.interconnessione_stato = 'non_interconnesso'

        machine.save(update_fields=['interconnessione_prevista', 'data_interconnessione_prevista',
                                     'interconnessione_stato', 'updated_at'])
        return Response({
            'interconnessione_stato': machine.interconnessione_stato,
            'interconnessione_prevista': machine.interconnessione_prevista,
            'data_interconnessione_prevista': machine.data_interconnessione_prevista,
        })

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def benefit_fiscal_documents(self, request, pk=None):
        """Caricamento di documenti per il beneficio fiscale."""
        machine = self.get_object()
        if get_user_office_code(request.user) != 'ADMIN' and not request.user.is_superuser:
            return Response({'error': 'Solo l’ufficio amministrazione può caricare questi documenti.'}, status=403)

        benefit, _ = MachineFiscalBenefit.objects.get_or_create(machine=machine)
        operation = request.data.get('operation')
        files = request.FILES.getlist('files')
        if not operation or not files:
            return Response({'error': 'Operazione e file sono obbligatori.'}, status=400)

        operation_label = dict(MachineFiscalBenefitDocument.OPERATION_CHOICES).get(operation, operation)
        created = []
        for uploaded_file in files:
            safe_file = build_safe_uploaded_file(uploaded_file)
            doc = MachineFiscalBenefitDocument(
                benefit=benefit,
                operation=operation,
                uploaded_by=request.user,
            )
            doc.file = safe_file
            doc.save()
            created.append(MachineFiscalBenefitDocumentSerializer(doc).data)
        return Response(created, status=201)

    @action(detail=True, methods=['delete'], url_path=r'benefit_fiscal_documents/(?P<doc_id>[^/.]+)')
    def delete_benefit_fiscal_document(self, request, pk=None, doc_id=None):
        """Elimina un documento del beneficio fiscale."""
        machine = self.get_object()
        benefit = get_object_or_404(MachineFiscalBenefit, machine=machine)
        doc = get_object_or_404(MachineFiscalBenefitDocument, pk=doc_id, benefit=benefit)

        user = request.user
        if not user.is_superuser and doc.uploaded_by_id != user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per eliminare questo documento del beneficio fiscale.')

        MachineAdminDocument.objects.filter(tipo_documento='ALTRO_ADMIN', numero_documento=f'BF-{doc.id}').delete()
        doc.delete()
        return Response(status=204)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def benefit_fiscal_maintenance(self, request, pk=None):
        """Aggiunge un anno di mantenimento e documenti associati."""
        machine = self.get_object()
        if get_user_office_code(request.user) != 'ADMIN' and not request.user.is_superuser:
            return Response({'error': 'Solo l’ufficio amministrazione può gestire il mantenimento.'}, status=403)

        benefit, _ = MachineFiscalBenefit.objects.get_or_create(machine=machine)
        anno = request.data.get('anno')
        if not anno:
            return Response({'error': 'L’anno è obbligatorio.'}, status=400)

        year = MachineFiscalBenefitMaintenanceYear.objects.create(benefit=benefit, anno=int(anno))
        files = request.FILES.getlist('files')
        for uploaded_file in files:
            safe_file = build_safe_uploaded_file(uploaded_file)
            doc = MachineFiscalBenefitMaintenanceDocument(
                year=year,
                uploaded_by=request.user,
            )
            doc.file = safe_file
            doc.save()
        return Response(MachineFiscalBenefitMaintenanceYearSerializer(year).data, status=201)

    @action(detail=True, methods=['post'])
    def close_benefit_fiscal(self, request, pk=None):
        """Chiude il beneficio fiscale."""
        machine = self.get_object()
        if get_user_office_code(request.user) != 'ADMIN' and not request.user.is_superuser:
            return Response({'error': 'Solo amministrazione può chiudere il beneficio fiscale.'}, status=403)
        benefit, _ = MachineFiscalBenefit.objects.get_or_create(machine=machine)
        benefit.chiuso = True
        benefit.save(update_fields=['chiuso', 'updated_at'])
        return Response(MachineFiscalBenefitSerializer(benefit).data)

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
        return Response({
            'totale': total,
            'attive': attive,
            'ferme': ferme,
            'in_manutenzione': manutenzione,
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
        uploaded_file = self.request.FILES.get('file') or self.request.FILES.get('files')
        safe_file = build_safe_uploaded_file(uploaded_file)
        file_name = uploaded_file.name if uploaded_file else ''
        document = serializer.save(
            machine=machine,
            uploaded_by=user,
            nome_file=file_name,
            file=safe_file,
        )
        if checklist_item:
            document.checklist_items.add(checklist_item)

    def perform_destroy(self, instance):
        self._ensure_access('write')
        user = self.request.user
        if not user.is_superuser and instance.uploaded_by_id != user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per eliminare questo documento tecnico.')
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
        uploaded_file = self.request.FILES.get('file') or self.request.FILES.get('files')
        safe_file = build_safe_uploaded_file(uploaded_file)
        serializer.save(machine=machine, uploaded_by=user, file=safe_file)

    def perform_destroy(self, instance):
        self._ensure_access('write')
        user = self.request.user
        if not user.is_superuser and instance.uploaded_by_id != user.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Non hai i permessi per eliminare questo documento amministrativo.')
        instance.delete()
