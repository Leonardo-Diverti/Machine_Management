from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count

from .models import Machine, MacchinaFase, DocumentoFase
from .serializers import (
    MachineSerializer,
    MachineCreateSerializer, 
    MachineChecklistSerializer, 
    MacchinaFaseSerializer,
    DocumentoFaseSerializer,
    get_user_office_code
)

class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all().order_by('-created_at')
    serializer_class = MachineSerializer 
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def create(self, request, *args, **kwargs):
        """Creazione nuovo macchinario da parte dell'ufficio tecnico."""
        office = get_user_office_code(request.user)
        if office not in ['TECH', 'ADMIN']:
            return Response(
                {"error": "Solo l'Ufficio Tecnico può creare nuovi macchinari."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = MachineCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Azione che fornisce i conteggi per la Dashboard del frontend."""
        total = Machine.objects.count()
        attive = Machine.objects.filter(stato='attiva').count()
        ferme = Machine.objects.filter(stato='ferma').count()
        in_manutenzione = Machine.objects.filter(stato='in_manutenzione').count()
        in_costruzione = Machine.objects.filter(stato='in_costruzione').count()
        dismesse = Machine.objects.filter(stato='dismessa').count()

        return Response({
            "totale": total,
            "total": total,
            "attive": attive,
            "ferme": ferme,
            "in_manutenzione": in_manutenzione,
            "in_costruzione": in_costruzione,
            "dismesse": dismesse
        })

    @action(detail=False, methods=['get'])
    def live_status(self, request):
        """Restituisce lo stato in tempo reale aggregato (pezzi buoni, fermi) dai log."""
        macchine = Machine.objects.all()
        live_data = []

        for m in macchine:
            pezzi_buoni = 0
            fermi_macchina = 0
            timestamp = timezone.now()
            
            log_manager = getattr(m, 'logs', getattr(m, 'machinestatuslog_set', None))
            
            if log_manager:
                ultimo_log = log_manager.order_by('-timestamp').first()
                if ultimo_log:
                    pezzi_buoni = getattr(ultimo_log, 'pezzi_buoni', 0)
                    fermi_macchina = getattr(ultimo_log, 'fermi_macchina', 0)
                    timestamp = getattr(ultimo_log, 'timestamp', timezone.now())

            live_data.append({
                "id_macchina": m.id,
                "cc": m.cc,
                "cdl": m.cdl,
                "stato": m.stato,
                "pezzi_buoni": pezzi_buoni,
                "fermi_macchina": fermi_macchina,
                "timestamp": timestamp
            })

        return Response(live_data)

    @action(detail=True, methods=['get'])
    def checklist(self, request, pk=None):
        """Restituisce la checklist delle fasi e documenti per il macchinario."""
        machine = self.get_object()
        serializer = MachineChecklistSerializer(machine, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path=r'fasi/(?P<fase_id>\d+)/toggle')
    def toggle_fase(self, request, fase_id=None):
        """Spunta o despunta una fase della checklist."""
        macchina_fase = get_object_or_404(MacchinaFase, id=fase_id)
        office = get_user_office_code(request.user)

        if office != 'ADMIN' and office != macchina_fase.fase.ufficio_competente:
            return Response(
                {"error": f"Non hai i permessi per modificare le fasi dell'ufficio {macchina_fase.fase.get_ufficio_competente_display()}."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not macchina_fase.completata:
            docs_mancanti = macchina_fase.documenti.filter(completato=False).exists()
            if docs_mancanti:
                return Response(
                    {"error": "Carica prima tutti i documenti obbligatori associati a questa fase."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        macchina_fase.completata = not macchina_fase.completata
        macchina_fase.data_completamento = timezone.now() if macchina_fase.completata else None
        macchina_fase.save()

        serializer = MacchinaFaseSerializer(macchina_fase, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path=r'documenti-fase/(?P<doc_id>\d+)/upload')
    def upload_documento_fase(self, request, doc_id=None):
        """Carica un file per un documento di fase e lo imposta come completato."""
        doc = get_object_or_404(DocumentoFase, id=doc_id)
        office = get_user_office_code(request.user)

        if office != 'ADMIN' and office != doc.macchina_fase.fase.ufficio_competente:
            return Response(
                {"error": "Non hai i permessi per inserire documenti in questa fase."},
                status=status.HTTP_403_FORBIDDEN
            )

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "Nessun file caricato."}, status=status.HTTP_400_BAD_REQUEST)

        doc.file = file_obj
        doc.completato = True
        doc.save()

        serializer = DocumentoFaseSerializer(doc)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cambia-stato')
    def cambia_stato(self, request, pk=None):
        """Passa la macchina da 'in_costruzione' a uno stato operativo (attiva, ferma, ecc.)."""
        machine = self.get_object()
        office = get_user_office_code(request.user)

        if office not in ['TECH', 'ADMIN']:
            return Response(
                {"error": "Solo l'Ufficio Tecnico può variare lo stato di operatività della macchina."},
                status=status.HTTP_403_FORBIDDEN
            )

        nuovo_stato = request.data.get('nuovo_stato')
        stati_validi = ['attiva', 'ferma', 'dismessa', 'in_manutenzione']

        if nuovo_stato not in stati_validi:
            return Response(
                {"error": f"Stato non valido. Scegli tra: {', '.join(stati_validi)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if machine.stato == 'in_costruzione':
            if not machine.check_tutte_fasi_completate():
                return Response(
                    {"error": "Impossibile passare in produzione: ci sono fasi o documenti non ancora completati."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        machine.stato = nuovo_stato
        machine.fase_operativa = nuovo_stato
        machine.save()

        return Response({
            "message": f"Stato della macchina aggiornato con successo a '{machine.get_stato_display()}'.",
            "stato": machine.stato
        })