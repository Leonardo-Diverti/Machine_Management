from rest_framework import serializers
from .models import (
    Machine, MachineITData, MachineTechData, MachineDocument, 
    MachineAdminDocument, MachineStatusLog, FaseCostruzione, 
    MacchinaFase, DocumentoFase
)

class MachineITDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineITData
        fields = '__all__'


class MachineTechDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineTechData
        fields = '__all__'


class MachineDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineDocument
        fields = '__all__'


class MachineAdminDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineAdminDocument
        fields = '__all__'


class MachineStatusLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineStatusLog
        fields = ['id', 'machine', 'stato', 'pezzi_buoni', 'fermi_macchina', 'timestamp']


class FaseCostruzioneSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaseCostruzione
        fields = '__all__'


class DocumentoFaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoFase
        fields = '__all__'


class MacchinaFaseSerializer(serializers.ModelSerializer):
    documenti = DocumentoFaseSerializer(many=True, read_only=True)
    fase_nome = serializers.CharField(source='fase.nome', read_only=True)
    ufficio_competente = serializers.CharField(source='fase.ufficio_competente', read_only=True)

    class Meta:
        model = MacchinaFase
        fields = ['id', 'machine', 'fase', 'fase_nome', 'ufficio_competente', 'completata', 'data_completamento', 'documenti']


class MachineListSerializer(serializers.ModelSerializer):
    latest_status = serializers.SerializerMethodField()

    class Meta:
        model = Machine
        fields = [
            'id', 'cdl', 'cc', 'capannone', 'anno_avviamento', 
            'stato', 'fase_operativa', 'tipo_acquisizione', 'updated_at', 
            'latest_status'
        ]

    def get_latest_status(self, obj):
        latest = obj.status_logs.order_by('-timestamp').first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None


class MachineSerializer(serializers.ModelSerializer):
    it_data = MachineITDataSerializer(read_only=True)
    tech_data = MachineTechDataSerializer(read_only=True)
    latest_status = serializers.SerializerMethodField()
    fasi_costruzione = MacchinaFaseSerializer(many=True, read_only=True)

    class Meta:
        model = Machine
        fields = [
            'id', 'cdl', 'cc', 'capannone', 'anno_avviamento', 
            'stato', 'fase_operativa', 'tipo_acquisizione', 'updated_at', 
            'it_data', 'tech_data', 'latest_status', 'fasi_costruzione'
        ]

    def get_latest_status(self, obj):
        latest = obj.status_logs.order_by('-timestamp').first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None


class MachineDetailSerializer(serializers.ModelSerializer):
    it_data = MachineITDataSerializer(read_only=True)
    tech_data = MachineTechDataSerializer(read_only=True)
    latest_status = serializers.SerializerMethodField()
    fasi_costruzione = MacchinaFaseSerializer(many=True, read_only=True)
    documents = MachineDocumentSerializer(many=True, read_only=True)
    admin_documents = MachineAdminDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Machine
        fields = [
            'id', 'cdl', 'cc', 'capannone', 'anno_avviamento', 
            'stato', 'fase_operativa', 'tipo_acquisizione', 'updated_at', 
            'it_data', 'tech_data', 'latest_status', 'fasi_costruzione', 
            'documents', 'admin_documents'
        ]

    def get_latest_status(self, obj):
        latest = obj.status_logs.order_by('-timestamp').first()
        if latest:
            return MachineStatusLogSerializer(latest).data
        return None