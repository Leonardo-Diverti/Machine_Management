# Questo file serializza i dati dei macchinari e dei documenti per le API.
from rest_framework import serializers
from .models import (Machine, MachineITData, MachineTechData,
                     MachineDocument, MachineAdminDocument, MachineStatusLog,
                     MachineChecklistItem)


class MachineITDataSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MachineITData
        fields = ['id', 'tipo_accentratore', 'indirizzo_ip', 'note_it',
                  'updated_at', 'updated_by', 'updated_by_name']
        read_only_fields = ['updated_at', 'updated_by', 'updated_by_name']

    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None


class MachineTechDataSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MachineTechData
        fields = ['id', 'descrizione_tecnica', 'marca', 'modello',
                  'anno_costruzione', 'note_tecniche', 'updated_at',
                  'updated_by', 'updated_by_name']
        read_only_fields = ['updated_at', 'updated_by', 'updated_by_name']

    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.username
        return None


class MachineDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', read_only=True
    )
    nome_file = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = MachineDocument
        fields = ['id', 'machine', 'tipo_documento', 'tipo_documento_display',
                  'nome_file', 'file', 'uploaded_by', 'uploaded_by_name',
                  'uploaded_at', 'note', 'checklist_items']
        read_only_fields = ['machine', 'uploaded_by', 'uploaded_by_name', 'uploaded_at',
                            'checklist_items']

    def validate(self, attrs):
        if 'file' in attrs and not attrs.get('nome_file'):
            attrs['nome_file'] = attrs['file'].name
        return attrs

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None


class MachineAdminDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    tipo_documento_display = serializers.CharField(
        source='get_tipo_documento_display', read_only=True
    )

    class Meta:
        model = MachineAdminDocument
        fields = ['id', 'machine', 'tipo_documento', 'tipo_documento_display',
                  'numero_documento', 'data_documento', 'importo', 'fornitore',
                  'descrizione', 'file', 'uploaded_by', 'uploaded_by_name',
                  'uploaded_at']
        read_only_fields = ['machine', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None


class MachineStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineStatusLog
        fields = ['id', 'machine', 'stato', 'pezzi_buoni', 'fermi_macchina',
                  'orario_fermo', 'motivo_fermo', 'timestamp']


class MachineChecklistItemSerializer(serializers.ModelSerializer):
    completata_da_name = serializers.SerializerMethodField()
    documents = MachineDocumentSerializer(many=True, read_only=True)
    document_requirements = serializers.SerializerMethodField()

    class Meta:
        model = MachineChecklistItem
        fields = ['id', 'codice', 'descrizione', 'ufficio', 'ordine',
                  'document_types', 'solo_visualizzazione_tech', 'completata',
                  'completata_at', 'completata_da', 'completata_da_name',
                  'documents', 'document_requirements']
        read_only_fields = ['completata_at', 'completata_da', 'completata_da_name',
                            'documents']

    def get_completata_da_name(self, obj):
        if obj.completata_da:
            return obj.completata_da.get_full_name() or obj.completata_da.username
        return None

    def get_document_requirements(self, obj):
        labels = dict(MachineDocument.TIPO_CHOICES)
        return [
            {'tipo_documento': document_type, 'label': labels.get(document_type, document_type)}
            for document_type in obj.document_types
        ]


class MachineListSerializer(serializers.ModelSerializer):
    """Serializer per la lista macchinari con ultimo stato"""
    latest_status = serializers.SerializerMethodField()
    checklist_progress = serializers.SerializerMethodField()
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)

    class Meta:
        model = Machine
        fields = [
            'id', 'cdl', 'cc', 'capannone', 'tipo_macchina', 'commessa',
            'commessa_macchina', 'commessa_automazione', 'anno_avviamento',
            'stato', 'stato_display', 'created_at', 'updated_at', 'latest_status',
            'checklist_progress'
        ]

    def get_latest_status(self, obj):
        latest = obj.status_logs.first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None

    def get_checklist_progress(self, obj):
        items = list(obj.checklist_items.all())
        return {
            'total': len(items),
            'completed': sum(item.completata for item in items),
        }


class MachineDetailSerializer(serializers.ModelSerializer):
    """Serializer completo per il dettaglio macchinario"""
    it_data = MachineITDataSerializer(read_only=True)
    tech_data = MachineTechDataSerializer(read_only=True)
    documents = MachineDocumentSerializer(many=True, read_only=True)
    admin_documents = MachineAdminDocumentSerializer(many=True, read_only=True)
    latest_status = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()
    checklist_items = MachineChecklistItemSerializer(many=True, read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)

    class Meta:
        model = Machine
        fields = ['id', 'cdl', 'cc', 'capannone', 'tipo_macchina', 'commessa',
              'commessa_macchina', 'commessa_automazione', 'anno_avviamento', 'stato',
                  'stato_display', 'created_at', 'updated_at',
                  'it_data', 'tech_data', 'documents', 'admin_documents',
              'latest_status', 'recent_logs', 'checklist_items']

    def validate(self, attrs):
        """Richiede le commesse coerenti con il tipo in fase di creazione."""
        if self.instance is not None:
            return attrs

        machine_type = attrs.get('tipo_macchina', 'COMPLESSA')
        if machine_type == 'ACQUISTO_DIRETTO':
            required = ['commessa']
        else:
            required = ['commessa_macchina', 'commessa_automazione']

        missing = [field for field in required if not attrs.get(field)]
        if missing:
            raise serializers.ValidationError({
                field: 'Questo campo è obbligatorio per il tipo di macchina selezionato.'
                for field in missing
            })
        return attrs

    def get_latest_status(self, obj):
        latest = obj.status_logs.first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None

    def get_recent_logs(self, obj):
        logs = obj.status_logs.all()[:20]
        return MachineStatusLogSerializer(logs, many=True).data
