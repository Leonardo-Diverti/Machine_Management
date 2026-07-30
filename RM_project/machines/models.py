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
        ('inserimento_db', 'Inserimento nel database'),
        ('ordinata', 'Ordinata'),
        ('in_costruzione', 'In costruzione'),
        ('attiva', 'Attiva'),
        ('in_manutenzione', 'In Manutenzione'),
        ('ferma', 'Ferma'),
    ]

    INTERCONNESSIONE_CHOICES = [
        ('non_interconnesso', 'Non interconnesso'),
        ('in_attesa', 'In attesa di interconnessione'),
        ('interconnessa', 'Interconnessa'),
    ]

    STABILIMENTO_CHOICES = [
        ('Campitello', 'Campitello'),
        ('Tubificio', 'Tubificio'),
        ('Pilastro', 'Pilastro'),
    ]

    cdl = models.CharField(max_length=50, blank=True, null=True, verbose_name="CDL")
    cc = models.CharField(max_length=50, blank=True, null=True, verbose_name="CC")
    capannone = models.CharField(max_length=50, verbose_name="Capannone")
    stabilimento = models.CharField(max_length=50, choices=STABILIMENTO_CHOICES, blank=True, null=True, verbose_name="Stabilimento")
    tipo_macchina = models.CharField(max_length=30, choices=MACHINE_TYPE_CHOICES,
                                     default='COMPLESSA',
                                     verbose_name="Tipo Macchina")
    commessa = models.JSONField(default=list, blank=True,
                                verbose_name="Commessa")
    commessa_macchina = models.JSONField(default=list, blank=True,
                                         verbose_name="Commessa Macchina")
    commessa_automazione = models.JSONField(default=list, blank=True,
                                            verbose_name="Commessa Automazione")
    anno_avviamento = models.IntegerField(blank=True, null=True, verbose_name="Anno di Avviamento")
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='inserimento_db',
                             verbose_name="Stato")
    # Campi fiscali (compilabili solo da ufficio amministrazione)
    id_investimento_rm = models.PositiveIntegerField(blank=True, null=True,
                                                      verbose_name="ID Investimento RM")
    id_investimento_consulente = models.PositiveIntegerField(blank=True, null=True,
                                                              verbose_name="ID Investimento Consulente")
    consulente = models.CharField(max_length=200, blank=True, null=True,
                                   verbose_name="Consulente")
    # Campi interconnessione (gestiti da ufficio IT)
    interconnessione_stato = models.CharField(max_length=20, choices=INTERCONNESSIONE_CHOICES,
                                               default='non_interconnesso',
                                               verbose_name="Stato Interconnessione")
    interconnessione_prevista = models.BooleanField(blank=True, null=True,
                                                     verbose_name="Interconnessione Prevista")
    data_interconnessione_prevista = models.DateField(blank=True, null=True,
                                                       verbose_name="Data Interconnessione Prevista")
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
        ('ORDINE_MACCHINA', 'Ordine di Acquisto'),
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


class MachineFiscalBenefit(models.Model):
    """Gestione del beneficio fiscale di una macchina in produzione."""
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, related_name='benefit_fiscal')
    attivo = models.BooleanField(default=False, verbose_name="Beneficio attivo")
    chiuso = models.BooleanField(default=False, verbose_name="Beneficio chiuso")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")

    class Meta:
        verbose_name = "Beneficio Fiscale"
        verbose_name_plural = "Benefici Fiscali"

    def __str__(self):
        return f"Beneficio fiscale - {self.machine.cdl} / {self.machine.cc}"


class MachineFiscalBenefitDocument(models.Model):
    """Documenti caricati per una singola voce del beneficio fiscale."""
    OPERATION_CHOICES = [
        ('fatture', 'Fatture'),
        ('documenti_trasporto', 'Documenti di trasporto'),
        ('ordini_acquisto', 'Ordini di acquisto'),
        ('contabili_pagamento', 'Contabili di pagamento'),
        ('perizia_asseverata', 'Perizia asseverata'),
        ('attestazione_contabile', 'Attestazione contabile'),
        ('comunicazione_preventiva', 'Comunicazione preventiva'),
        ('comunicazione_intermedia', 'Comunicazione intermedia'),
        ('comunicazione_consuntivo', 'Comunicazione a consuntivo'),
    ]

    benefit = models.ForeignKey(MachineFiscalBenefit, on_delete=models.CASCADE, related_name='documents')
    operation = models.CharField(max_length=40, choices=OPERATION_CHOICES, verbose_name="Operazione")
    file = models.FileField(upload_to='documents/fiscal_benefit/', verbose_name="File")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='fiscal_benefit_docs', verbose_name="Caricato da")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Upload")

    class Meta:
        verbose_name = "Documento Beneficio Fiscale"
        verbose_name_plural = "Documenti Beneficio Fiscale"
        ordering = ['-uploaded_at']


class MachineFiscalBenefitMaintenanceYear(models.Model):
    """Anni di mantenimento del beneficio fiscale."""
    benefit = models.ForeignKey(MachineFiscalBenefit, on_delete=models.CASCADE, related_name='maintenance_years')
    anno = models.IntegerField(verbose_name="Anno")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")

    class Meta:
        verbose_name = "Anno Mantenimento"
        verbose_name_plural = "Anni Mantenimento"
        ordering = ['anno']


class MachineFiscalBenefitMaintenanceDocument(models.Model):
    """Documento di comunicazione periodica associato a un anno di mantenimento."""
    year = models.ForeignKey(MachineFiscalBenefitMaintenanceYear, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/fiscal_benefit/maintenance/', verbose_name="File")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='maintenance_docs', verbose_name="Caricato da")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Upload")

    class Meta:
        verbose_name = "Documento Mantenimento"
        verbose_name_plural = "Documenti Mantenimento"
        ordering = ['-uploaded_at']


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
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    class Meta:
        verbose_name = "Log Stato Macchinario"
        verbose_name_plural = "Log Stato Macchinari"
        ordering = ['-timestamp']

    def __str__(self):
        return f"CDL {self.machine.cdl} / CC {self.machine.cc} - {self.stato} @ {self.timestamp}"
