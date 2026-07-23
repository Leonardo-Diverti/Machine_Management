from django.db import models

class Machine(models.Model):
    TIPO_ACQUISIZIONE_CHOICES = [
        ('COMPLESSA', 'Macchina Complessa'),
        ('DIRETTA', 'Ad Acquisto Diretto'),
    ]

    STATO_CHOICES = [
        ('in_costruzione', 'In Costruzione'),
        ('attiva', 'Attiva'),
        ('ferma', 'Ferma'),
        ('in_manutenzione', 'In Manutenzione'),
        ('dismessa', 'Dismessa'),
    ]

    capannone = models.CharField(max_length=50)
    anno_avviamento = models.IntegerField(null=True, blank=True)
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='in_costruzione')
    cc = models.CharField(max_length=50, null=True, blank=True, verbose_name="Centro di Costo")
    cdl = models.CharField(max_length=50, null=True, blank=True, verbose_name="Centro di Lavoro")
    fase_operativa = models.CharField(max_length=20, default='in_costruzione')
    tipo_acquisizione = models.CharField(max_length=20, choices=TIPO_ACQUISIZIONE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Macchinario"
        verbose_name_plural = "Macchinari"

    def __str__(self):
        return f"Macchina {self.id} - {self.capannone} ({self.get_tipo_acquisizione_display()})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Se il macchinario è appena stato creato ed è in_costruzione, genera le fasi
        if is_new and self.stato == 'in_costruzione':
            self.genera_fasi_costruzione()

    def genera_fasi_costruzione(self):
        """Genera automaticamente la lista di controllo delle fasi e associa i relativi documenti."""
        fasi_applicabili = FaseCostruzione.objects.filter(
            models.Q(tipo_macchina_applicabile=self.tipo_acquisizione) |
            models.Q(tipo_macchina_applicabile='ENTRAMBE')
        ).order_by('ordine')

        for fase in fasi_applicabili:
            macchina_fase = MacchinaFase.objects.create(
                machine=self,
                fase=fase,
                completata=False
            )

            # Associazione automatica dei documenti richiesti
            nome_fase_lower = fase.nome.strip().lower()

            if "entrata merci" in nome_fase_lower:
                DocumentoFase.objects.create(
                    macchina_fase=macchina_fase,
                    nome_documento="Documento di Trasporto",
                    completato=False
                )
            elif "posizionamento" in nome_fase_lower:
                DocumentoFase.objects.create(
                    macchina_fase=macchina_fase,
                    nome_documento="Manuale di uso e manutenzione",
                    completato=False
                )
                DocumentoFase.objects.create(
                    macchina_fase=macchina_fase,
                    nome_documento="Certificato CE",
                    completato=False
                )

    def check_tutte_fasi_completate(self):
        """Verifica se tutte le fasi e tutti i documenti obbligatori sono stati completati."""
        fasi_incomplete = self.fasi.filter(completata=False).exists()
        docs_incompleti = DocumentoFase.objects.filter(
            macchina_fase__machine=self, 
            completato=False
        ).exists()
        return not (fasi_incomplete or docs_incompleti)


class FaseCostruzione(models.Model):
    OFFICE_CHOICES = [
        ('TECH', 'Ufficio Tecnico'),
        ('IT', 'Ufficio Informatico'),
        ('ADMIN', 'Amministrazione'),
    ]

    TIPO_APPLICABILE_CHOICES = [
        ('COMPLESSA', 'Macchina Complessa'),
        ('DIRETTA', 'Ad Acquisto Diretto'),
        ('ENTRAMBE', 'Entrambe'),
    ]

    nome = models.CharField(max_length=100)
    ordine = models.IntegerField(default=0)
    tipo_macchina_applicabile = models.CharField(
        max_length=20, 
        choices=TIPO_APPLICABILE_CHOICES, 
        default='ENTRAMBE'
    )
    ufficio_competente = models.CharField(max_length=10, choices=OFFICE_CHOICES)

    class Meta:
        verbose_name = "Fase di Costruzione"
        verbose_name_plural = "Fasi di Costruzione"
        ordering = ['ordine']

    def __str__(self):
        return f"{self.ordine}. {self.nome} ({self.ufficio_competente})"


class MacchinaFase(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='fasi')
    fase = models.ForeignKey(FaseCostruzione, on_delete=models.CASCADE)
    completata = models.BooleanField(default=False)
    data_completamento = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Fase Macchina"
        verbose_name_plural = "Fasi Macchina"
        ordering = ['fase__ordine']

    def __str__(self):
        stato = "✓" if self.completata else "✗"
        return f"[{stato}] {self.machine} - {self.fase.nome}"


class DocumentoFase(models.Model):
    macchina_fase = models.ForeignKey(MacchinaFase, on_delete=models.CASCADE, related_name='documenti')
    nome_documento = models.CharField(max_length=100)
    file = models.FileField(upload_to='documenti_fasi/', null=True, blank=True)
    completato = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Documento Fase"
        verbose_name_plural = "Documenti Fase"

    def __str__(self):
        return f"{self.nome_documento} ({'Caricato' if self.completato else 'Mancante'})"