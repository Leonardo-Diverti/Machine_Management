from rest_framework import serializers
from .models import Machine, FaseCostruzione, MacchinaFase, DocumentoFase

def get_user_office_code(user):
    """Determina il codice dell'ufficio dell'utente in base ai gruppi."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'ADMIN'
    
    if hasattr(user, 'userprofile') and user.userprofile.office:
        return user.userprofile.office.code.upper()

    if user.groups.filter(name__in=['admin_tech', 'TECH', 'Ufficio Tecnico']).exists():
        return 'TECH'
    if user.groups.filter(name__in=['admin_it', 'IT', 'Ufficio Informatico']).exists():
        return 'IT'
    if user.groups.filter(name__in=['admin_amm', 'ADMIN', 'Amministrazione']).exists():
        return 'ADMIN'
        
    return None


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'


class MachineCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ['id', 'capannone', 'anno_avviamento', 'cc', 'cdl', 'tipo_acquisizione', 'stato']
        read_only_fields = ['stato']


class DocumentoFaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentoFase
        fields = ['id', 'nome_documento', 'file', 'completato']


class MacchinaFaseSerializer(serializers.ModelSerializer):
    nome_fase = serializers.CharField(source='fase.nome', read_only=True)
    ordine = serializers.IntegerField(source='fase.ordine', read_only=True)
    ufficio_competente = serializers.CharField(source='fase.ufficio_competente', read_only=True)
    documenti = DocumentoFaseSerializer(many=True, read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_view = serializers.SerializerMethodField()

    class Meta:
        model = MacchinaFase
        fields = [
            'id', 'fase_id', 'nome_fase', 'ordine', 
            'ufficio_competente', 'completata', 
            'data_completamento', 'can_edit', 'can_view', 'documenti'
        ]

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        office = get_user_office_code(request.user)
        if office == 'ADMIN':
            return True
        return office == obj.fase.ufficio_competente

    def get_can_view(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        office = get_user_office_code(request.user)
        if office in ['ADMIN', 'TECH', 'IT']:
            return True
        return False


class MachineChecklistSerializer(serializers.ModelSerializer):
    fasi = serializers.SerializerMethodField()
    tutte_fasi_completate = serializers.SerializerMethodField()

    class Meta:
        model = Machine
        fields = [
            'id', 'capannone', 'cc', 'cdl', 'stato', 
            'tipo_acquisizione', 'tutte_fasi_completate', 'fasi'
        ]

    def get_fasi(self, obj):
        fasi_qs = obj.fasi.all().select_related('fase').prefetch_related('documenti')
        return MacchinaFaseSerializer(fasi_qs, many=True, context=self.context).data

    def get_tutte_fasi_completate(self, obj):
        return obj.check_tutte_fasi_completate()