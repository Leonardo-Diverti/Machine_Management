# Questo file definisce i modelli dei macchinari, dati IT, tecnici e log di stato.
from django.db import models
from django.contrib.auth.models import User


class Machine(models.Model):
    """Anagrafica macchinari"""
    STATO_CHOICES = [
        ('attiva', 'Attiva'),
        ('in_manutenzione', 'In Manutenzione'),
        ('ferma', 'Ferma'),
        ('dismessa', 'Dismessa'),
    ]

    matricola = models.CharField(max_length=50, unique=True, verbose_name="Matricola")
    capannone = models.CharField(max_length=50, verbose_name="Capannone")
    anno_avviamento = models.IntegerField(blank=True, null=True, verbose_name="Anno di Avviamento")
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='attiva',
                             verbose_name="Stato")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Creazione")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")

    class Meta:
        verbose_name = "Macchinario"
        verbose_name_plural = "Macchinari"
        ordering = ['matricola']

    def __str__(self):
        return f"{self.matricola} - {self.capannone}"


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
        return f"IT Data: {self.machine.matricola}"


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
        return f"Tech Data: {self.machine.matricola}"


class MachineDocument(models.Model):
    """Documenti tecnici del macchinario"""
    TIPO_CHOICES = [
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
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='uploaded_docs', verbose_name="Caricato da")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Upload")
    note = models.TextField(blank=True, null=True, verbose_name="Note")

    class Meta:
        verbose_name = "Documento Tecnico"
        verbose_name_plural = "Documenti Tecnici"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.machine.matricola}"


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
        return f"{self.get_tipo_documento_display()} {self.numero_documento} - {self.machine.matricola}"


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
        return f"{self.machine.matricola} - {self.stato} @ {self.timestamp}"
