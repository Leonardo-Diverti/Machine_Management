# Questo file registra i modelli amministrativi dell'app machines.
from django.contrib import admin
from .models import (Machine, MachineITData, MachineTechData,
                     MachineDocument, MachineAdminDocument, MachineStatusLog,
                     MachineChecklistItem)


class MachineITDataInline(admin.StackedInline):
    model = MachineITData
    extra = 0


class MachineTechDataInline(admin.StackedInline):
    model = MachineTechData
    extra = 0


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('cdl', 'cc', 'capannone', 'tipo_macchina', 'anno_avviamento', 'stato', 'updated_at')
    list_filter = ('tipo_macchina', 'stato', 'capannone')
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


@admin.register(MachineChecklistItem)
class MachineChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('machine', 'ufficio', 'descrizione', 'completata', 'completata_da',
                    'completata_at')
    list_filter = ('ufficio', 'completata', 'machine__tipo_macchina')
    search_fields = ('machine__cdl', 'machine__cc', 'descrizione')
