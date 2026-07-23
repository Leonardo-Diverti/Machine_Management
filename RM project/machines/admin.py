# Questo file registra i modelli amministrativi dell'app machines.
from django.contrib import admin
from .models import (
    Machine, MachineITData, MachineTechData, MachineDocument, 
    MachineAdminDocument, MachineStatusLog, FaseCostruzione, 
    MacchinaFase, DocumentoFase
)

class MachineITDataInline(admin.StackedInline):
    model = MachineITData
    extra = 0

class MachineTechDataInline(admin.StackedInline):
    model = MachineTechData
    extra = 0

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('cdl', 'cc', 'capannone', 'anno_avviamento', 'stato', 'fase_operativa', 'tipo_acquisizione', 'updated_at')
    list_filter = ('stato', 'capannone', 'fase_operativa', 'tipo_acquisizione')
    search_fields = ('cdl', 'cc', 'capannone')
    inlines = [MachineITDataInline, MachineTechDataInline]

@admin.register(MachineDocument)
class MachineDocumentAdmin(admin.ModelAdmin):
    list_display = ('machine', 'tipo_documento', 'nome_file', 'uploaded_by', 'uploaded_at')
    list_filter = ('tipo_documento',)

@admin.register(MachineAdminDocument)
class MachineAdminDocumentAdmin(admin.ModelAdmin):
    list_display = ('machine', 'tipo_documento', 'numero_documento', 'importo', 'data_documento')
    list_filter = ('tipo_documento',)

@admin.register(MachineStatusLog)
class MachineStatusLogAdmin(admin.ModelAdmin):
    list_display = ('machine', 'stato', 'pezzi_buoni', 'fermi_macchina', 'timestamp')
    list_filter = ('stato',)

@admin.register(FaseCostruzione)
class FaseCostruzioneAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ordine', 'tipo_macchina_applicabile', 'ufficio_competente')
    list_filter = ('tipo_macchina_applicabile', 'ufficio_competente')
    search_fields = ('nome',)

@admin.register(MacchinaFase)
class MacchinaFaseAdmin(admin.ModelAdmin):
    list_display = ('machine', 'fase', 'completata', 'data_completamento')
    list_filter = ('completata', 'fase')
    search_fields = ('machine__cdl', 'fase__nome')

@admin.register(DocumentoFase)
class DocumentoFaseAdmin(admin.ModelAdmin):
    list_display = ('macchina_fase', 'nome_documento', 'completato')
    list_filter = ('completato',)
    search_fields = ('nome_documento',)