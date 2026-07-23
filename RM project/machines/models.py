# Questo file definisce i modelli dei macchinari, dati IT, tecnici e log di stato.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Machine(models.Model):
    """Anagrafica macchinari"""
    STATO_CHOICES = [
        ('attiva', 'Attiva'),
        ('in_manutenzione', 'In Manutenzione'),
        ('ferma', 'Ferma'),
        ('dismessa', 'Dismessa'),
    ]
    FASE_OPERATIVA_CHOICES = [
        ('COSTRUZIONE', 'In Costruzione'),
        ('PRODUZIONE', 'In Produzione'),
    ]
    TIPO_ACQUISIZIONE_CHOICES = [
        ('COMPLESSA', 'Complessa'),
        ('DIRETTA', 'Acquisto Diretto'),
    ]

    fase_operativa = models.CharField(
        max_length=20, 
        choices=FASE_OPERATIVA_CHOICES, 
        default='COSTRUZIONE'
    )
    tipo_acquisizione = models.CharField(
        max_length=20, 
        choices=TIPO_ACQUISIZIONE_CHOICES, 
        default='DIRETTA'
    )

    cdl = models.CharField(max_length=50, blank=True, null=True, verbose_name="CDL")
    cc = models.CharField(max_length=50, blank=True, null=True, verbose_name="CC")
    capannone = models.CharField(max_length=50, verbose_name="Capannone")
    anno_avviamento = models.IntegerField(blank=True, null=True, verbose_name="Anno di Avviamento")
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='attiva', verbose_name="Stato")
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
    tipo_accentratore = models.CharField(max_length=10, choices=ACCENTRATORE_CHOICES, blank=True, null=True, verbose_name="Tipo Accentratore")
    indirizzo_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name="Indirizzo IP")
    note_it = models.TextField(blank=True, null=True, verbose_name="Note IT")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='it_updates', verbose_name="Aggiornato da")

    class Meta:
        verbose_name = "Dati IT Macchinario"
        verbose_name_plural = "Dati IT Macchinari"

    def __str__(self):
        return f"IT Data: {self.machine.cdl} - {self.machine.cc}"


class MachineTechData(models.Model):
    """Dati tecnici del macchinario"""
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, related_name='tech_data')
    descrizione_tecnica = models.TextField(blank=True, null=True, verbose_name="Descrizione Tecnica")
    marca = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca")
    modello = models.CharField(max_length=100, blank=True, null=True, verbose_name="Modello")
    anno_costruzione = models.IntegerField(blank=True, null=True, verbose_name="Anno di Costruzione")
    note_tecniche = models.TextField(blank=True, null=True, verbose_name="Note Tecniche")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ultimo Aggiornamento")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='tech_updates', verbose_name="Aggiornato da")

    class Meta:
        verbose_name = "Dati Tecnici Macchinario"
        verbose_name_plural = "Dati Tecnici Macchinari"

    def __str__(self):
        return f"Tech Data: CDL {self.machine.cdl} / CC {self.machine.cc}"


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
    tipo_documento = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo Documento")
    nome_file = models.CharField(max_length=255, verbose_name="Nome File")
    file = models.FileField(upload_to='documents/tech/', verbose_name="File")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_docs', verbose_name="Caricato da")
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
    tipo_documento = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo Documento")
    numero_documento = models.CharField(max_length=50, verbose_name="Numero Documento")
    data_documento = models.DateField(verbose_name="Data Documento")
    importo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Importo €")
    fornitore = models.CharField(max_length=200, blank=True, null=True, verbose_name="Fornitore")
    descrizione = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    file = models.FileField(upload_to='documents/admin/', blank=True, null=True, verbose_name="File")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_admin_docs', verbose_name="Caricato da")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Data Upload")

    class Meta:
        verbose_name = "Documento Amministrativo"
        verbose_name_plural = "Documenti Amministrativi"
        ordering = ['-data_documento']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} {self.numero_documento} - CDL {self.machine.cdl} / CC {self.machine.cc}"


class MachineStatusLog(models.Model):
    """Log stato e contatori dal PLC (simulato)"""
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='status_logs')
    stato = models.CharField(max_length=20, verbose_name="Stato")
    pezzi_buoni = models.IntegerField(default=0, verbose_name="Pezzi Buoni")
    fermi_macchina = models.IntegerField(default=0, verbose_name="Fermi Macchina")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp")

    class Meta:
        verbose_name = "Log Stato Macchinario"
        verbose_name_plural = "Log Stato Macchinari"
        ordering = ['-timestamp']

    def __str__(self):
        return f"CDL {self.machine.cdl} / CC {self.machine.cc} - {self.stato} @ {self.timestamp}"


class FaseCostruzione(models.Model):
    """Definisce il catalogo delle fasi possibili"""
    nome = models.CharField(max_length=100)
    ordine = models.IntegerField(default=0)
    tipo_macchina_applicabile = models.CharField(max_length=20, choices=Machine.TIPO_ACQUISIZIONE_CHOICES, null=True, blank=True)
    
    UFFICIO_CHOICES = [
        ('TECH', 'Ufficio Tecnico'),
        ('IT', 'Ufficio Informatico'),
    ]
    ufficio_competente = models.CharField(max_length=10, choices=UFFICIO_CHOICES, default='TECH')

    def __str__(self):
        return f"{self.nome} ({self.ufficio_competente})"


class MacchinaFase(models.Model):
    """Lega una specifica macchina alle sue fasi"""
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='fasi_costruzione')
    fase = models.ForeignKey(FaseCostruzione, on_delete=models.PROTECT)
    completata = models.BooleanField(default=False)
    data_completamento = models.DateTimeField(null=True, blank=True)


class DocumentoFase(models.Model):
    """Definisce quali documenti servono per una specifica MacchinaFase"""
    macchina_fase = models.ForeignKey(MacchinaFase, on_delete=models.CASCADE, related_name='documenti')
    nome_documento = models.CharField(max_length=100)
    file = models.FileField(upload_to='fasi_costruzione/', null=True, blank=True)
    completato = models.BooleanField(default=False)


@receiver(post_save, sender=Machine)
def crea_fasi_costruzione(sender, instance, created, **kwargs):
    if created:
        fasi_catalogo = FaseCostruzione.objects.filter(
            tipo_macchina_applicabile=instance.tipo_acquisizione
        ).order_by('ordine')
        
        for fase_base in fasi_catalogo:
            macchina_fase = MacchinaFase.objects.create(
                machine=instance,
                fase=fase_base,
                completata=False
            )
            
            nome_fase = fase_base.nome.lower()
            
            if instance.tipo_acquisizione == 'COMPLESSA':
                if nome_fase == 'entrata merci':
                    DocumentoFase.objects.create(macchina_fase=macchina_fase, nome_documento='Documento di trasporto')
                elif nome_fase == 'posizionamento macchina':
                    DocumentoFase.objects.create(macchina_fase=macchina_fase, nome_documento='Manuale di uso e manutenzione')
                    DocumentoFase.objects.create(macchina_fase=macchina_fase, nome_documento='Certificato CE')
                    
            elif instance.tipo_acquisizione == 'DIRETTA':
                if nome_fase == 'entrata merci':
                    DocumentoFase.objects.create(macchina_fase=macchina_fase, nome_documento='Documento di trasporto')
                elif nome_fase == 'manuale di uso e manutenzione':
                    DocumentoFase.objects.create(macchina_fase=macchina_fase, nome_documento='Manuale di uso e manutenzione')
                elif nome_fase == 'certificazione ce':
                    DocumentoFase.objects.create(macchina_fase=macchina_fase, nome_documento='Certificazione CE')