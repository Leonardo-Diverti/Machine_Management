# Questo file serializza i dati dei macchinari e dei documenti per le API.
from rest_framework import serializers
from .models import (Machine, MachineITData, MachineTechData,
                     MachineDocument, MachineAdminDocument, MachineStatusLog)


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
                  'uploaded_at', 'note']
        read_only_fields = ['machine', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']

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


class MachineListSerializer(serializers.ModelSerializer):
    """Serializer per la lista macchinari con ultimo stato"""
    latest_status = serializers.SerializerMethodField()
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)

    class Meta:
        model = Machine
        fields = ['id', 'cdl','cc', 'capannone', 'anno_avviamento', 'stato',
                  'stato_display', 'created_at', 'updated_at', 'latest_status']

    def get_latest_status(self, obj):
        latest = obj.status_logs.first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None


class MachineDetailSerializer(serializers.ModelSerializer):
    """Serializer completo per il dettaglio macchinario"""
    it_data = MachineITDataSerializer(read_only=True)
    tech_data = MachineTechDataSerializer(read_only=True)
    documents = MachineDocumentSerializer(many=True, read_only=True)
    admin_documents = MachineAdminDocumentSerializer(many=True, read_only=True)
    latest_status = serializers.SerializerMethodField()
    recent_logs = serializers.SerializerMethodField()
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)

    class Meta:
        model = Machine
        fields = ['id', 'cdl', 'cc', 'capannone', 'anno_avviamento', 'stato',
                  'stato_display', 'created_at', 'updated_at',
                  'it_data', 'tech_data', 'documents', 'admin_documents',
                  'latest_status', 'recent_logs']

    def get_latest_status(self, obj):
        latest = obj.status_logs.first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None

    def get_recent_logs(self, obj):
        logs = obj.status_logs.all()[:20]
        return MachineStatusLogSerializer(logs, many=True).data
