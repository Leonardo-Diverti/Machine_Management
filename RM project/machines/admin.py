from django.contrib import admin
from .models import Machine, FaseCostruzione, MacchinaFase, DocumentoFase

class DocumentoFaseInline(admin.TabularInline):
    model = DocumentoFase
    extra = 0

class MacchinaFaseInline(admin.TabularInline):
    model = MacchinaFase
    extra = 0
    readonly_fields = ('data_completamento',)

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('id', 'capannone', 'tipo_acquisizione', 'stato', 'created_at')
    list_filter = ('tipo_acquisizione', 'stato', 'capannone')
    search_fields = ('capannone', 'cc', 'cdl')
    inlines = [MacchinaFaseInline]

@admin.register(FaseCostruzione)
class FaseCostruzioneAdmin(admin.ModelAdmin):
    list_display = ('ordine', 'nome', 'ufficio_competente', 'tipo_macchina_applicabile')
    list_filter = ('ufficio_competente', 'tipo_macchina_applicabile')
    search_fields = ('nome',)
    ordering = ('ordine',)

@admin.register(MacchinaFase)
class MacchinaFaseAdmin(admin.ModelAdmin):
    list_display = ('machine', 'fase', 'completata', 'data_completamento')
    list_filter = ('completata', 'fase__ufficio_competente')
    inlines = [DocumentoFaseInline]

@admin.register(DocumentoFase)
class DocumentoFaseAdmin(admin.ModelAdmin):
    list_display = ('nome_documento', 'macchina_fase', 'completato', 'file')
    list_filter = ('completato',)