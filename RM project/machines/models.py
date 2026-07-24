# Questo file definisce i modelli dei macchinari, dati IT, tecnici e log di stato.
from django.db import models
from django.contrib.auth.models import User


class Machine(models.Model):
    """Anagrafica macchinari"""
    MACHINE_TYPE_CHOICES = [
        ('COMPLESSA', 'Macchina complessa'),
        ('ACQUISTO_DIRETTO', 'Macchina ad acquisto diretto'),
    ]

    STATO_CHOICES = [
        ('in_costruzione', 'In costruzione'),
        ('attiva', 'Attiva'),
        ('in_manutenzione', 'In Manutenzione'),
        ('ferma', 'Ferma'),
        ('dismessa', 'Dismessa'),
    ]

    cdl = models.CharField(max_length=50, blank=True, null=True, verbose_name="CDL")
    cc = models.CharField(max_length=50, blank=True, null=True, verbose_name="CC")
    capannone = models.CharField(max_length=50, verbose_name="Capannone")
    tipo_macchina = models.CharField(max_length=30, choices=MACHINE_TYPE_CHOICES,
                                     default='COMPLESSA',
                                     verbose_name="Tipo Macchina")
    commessa = models.CharField(max_length=100, blank=True, null=True,
                                verbose_name="Commessa")
    commessa_macchina = models.CharField(max_length=100, blank=True, null=True,
                                         verbose_name="Commessa Macchina")
    commessa_automazione = models.CharField(max_length=100, blank=True, null=True,
                                            verbose_name="Commessa Automazione")
    anno_avviamento = models.IntegerField(blank=True, null=True, verbose_name="Anno di Avviamento")
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='in_costruzione',
                             verbose_name="Stato")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")

    class Meta:
        verbose_name = "Macchinario"
        verbose_name_plural = "Macchinari"
        ordering = ['cdl', 'cc']

    def __str__(self):
       return f"CDL: {self.cdl} | CC: {self.cc} - {self.capannone}"


class MachineITData(models.Model):
    """Dati IT del macchinario"""
    ACCENTRATORE_CHOICES = [
        ('IOX', 'IOX'),
        ('RIO', 'RIO'),
        ('PLC', 'PLC'),
    ]

    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, related_name='it_data')
    tipo_accentratore = models.CharField(max_length=10, choices=ACCENTRATORE_CHOICES,
                                          blank=True, null=True,
                                          verbose_name="Tipo Accentratore")
    indirizzo_ip = models.GenericIPAddressField(blank=True, null=True,
                                                  verbose_name="Indirizzo IP")
    note_it = models.TextField(blank=True, null=True, verbose_name="Note IT")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                    related_name='it_updates', verbose_name="Aggiornato da")

    class Meta:
        verbose_name = "Dati IT Macchinario"
        verbose_name_plural = "Dati IT Macchinari"

    def __str__(self):
        return f"IT Data: {self.machine.cdl} - {self.machine.cc}"


class MachineTechData(models.Model):
    """Dati tecnici del macchinario"""
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, related_name='tech_data')
    descrizione_tecnica = models.TextField(blank=True, null=True,
                                            verbose_name="Descrizione Tecnica")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca")
    modello = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modello")
    anno_costruzione = models.IntegerField(blank=True, null=True,
                                            verbose_name="Anno di Costruzione")
    note_tecniche = models.TextField(blank=True, null=True, verbose_name="Note Tecniche")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                                    related_name='tech_updates', verbose_name="Aggiornato da")

    class Meta:
        verbose_name = "Dati Tecnici Macchinario"
        verbose_name_plural = "Dati Tecnici Macchinari"

    def __str__(self):
        return f"Tech Data: CDL {self.machine.cdl} / CC {self.machine.cc}"


class MachineDocument(models.Model):
    """Documenti tecnici del macchinario"""
    TIPO_CHOICES = [
        ('BOLLA_TRASPORTO', 'Documento di Trasporto'),
        ('USO_MANUTENZIONE', 'Manuale Uso e Manutenzione'),
        ('CERTIFICAZIONE_CE', 'Certificazione CE'),
        ('SCHEDA_VDR', 'Scheda VDR'),
        ('VERBALE_COLLAUDO', 'Verbale di Collaudo'),
        ('ALTRO', 'Altro'),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='documents')
    tipo_documento = models.CharField(max_length=30, choices=TIPO_CHOICES,
                                       verbose_name="Tipo Documento")
    nome_file = models.CharField(max_length=255, verbose_name="Nome File")
    file = models.FileField(upload_to='documents/tech/', verbose_name="File")
    checklist_items = models.ManyToManyField(
        'MachineChecklistItem', blank=True, related_name='documents'
    )
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='uploaded_docs', verbose_name="Caricato da")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Upload")
    note = models.TextField(blank=True, null=True, verbose_name="Note")

    class Meta:
        verbose_name = "Documento Tecnico"
        verbose_name_plural = "Documenti Tecnici"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - CDL {self.machine.cdl} / CC {self.machine.cc}"


class MachineAdminDocument(models.Model):
    """Documenti amministrativi del macchinario"""
    TIPO_CHOICES = [
        ('FATTURA', 'Fattura'),
        ('BOLLA_TRASPORTO', 'Bolla di Trasporto'),
        ('ORDINE_ACQUISTO', 'Ordine di Acquisto'),
        ('COPIA_PAGAMENTO', 'Copia Pagamento'),
        ('PERIZIA_CONSULENTE', 'Perizia consulente'),
        ('ALTRO_ADMIN', 'Altro'),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='admin_documents')
    tipo_documento = models.CharField(max_length=30, choices=TIPO_CHOICES,
                                       verbose_name="Tipo Documento")
    numero_documento = models.CharField(max_length=50, verbose_name="Numero Documento")
    data_documento = models.DateField(verbose_name="Data Documento")
    importo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                   verbose_name="Importo €")
    fornitore = models.CharField(max_length=200, blank=True, null=True, verbose_name="Fornitore")
    descrizione = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    file = models.FileField(upload_to='documents/admin/', blank=True, null=True,
                             verbose_name="File")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='uploaded_admin_docs',
                                     verbose_name="Caricato da")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Upload")

    class Meta:
        verbose_name = "Documento Amministrativo"
        verbose_name_plural = "Documenti Amministrativi"
        ordering = ['-data_documento']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} {self.numero_documento} - CDL {self.machine.cdl} / CC {self.machine.cc}"


class MachineChecklistItem(models.Model):
    """Attivita' di avviamento assegnate a una macchina."""
    OFFICE_CHOICES = [
        ('TECH', 'Ufficio Tecnico'),
        ('IT', 'Ufficio IT'),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE,
                                related_name='checklist_items')
    codice = models.CharField(max_length=80)
    descrizione = models.CharField(max_length=200)
    ufficio = models.CharField(max_length=10, choices=OFFICE_CHOICES)
    ordine = models.PositiveIntegerField(default=0)
    document_types = models.JSONField(default=list, blank=True)
    solo_visualizzazione_tech = models.BooleanField(default=False)
    completata = models.BooleanField(default=False)
    completata_at = models.DateTimeField(blank=True, null=True)
    completata_da = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='completed_checklist_items'
    )

    class Meta:
        ordering = ['ufficio', 'ordine', 'id']
        unique_together = ('machine', 'codice')

    def __str__(self):
        return f"{self.machine} - {self.descrizione}"


class MachineStatusLog(models.Model):
    """Log stato e contatori dal PLC (simulato)"""
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='status_logs')
    stato = models.CharField(max_length=20, verbose_name="Stato")
    pezzi_buoni = models.IntegerField(default=0, verbose_name="Pezzi Buoni")
    fermi_macchina = models.IntegerField(default=0, verbose_name="Fermi Macchina")
    orario_fermo = models.DateTimeField(blank=True, null=True, verbose_name="Orario Fermo")
    motivo_fermo = models.CharField(max_length=200, blank=True, null=True,
                                     verbose_name="Motivo Fermo")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    class Meta:
        verbose_name = "Log Stato Macchinario"
        verbose_name_plural = "Log Stato Macchinari"
        ordering = ['-timestamp']

    def __str__(self):
        return f"CDL {self.machine.cdl} / CC {self.machine.cc} - {self.stato} @ {self.timestamp}"
