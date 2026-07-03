from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Office(models.Model):
    """Ufficio / Ruolo aziendale"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome Ufficio")
    code = models.CharField(max_length=20, unique=True, verbose_name="Codice")
    description = models.TextField(blank=True, null=True, verbose_name="Descrizione")
    color = models.CharField(max_length=7, blank=True, null=True, verbose_name="Colore HEX")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="Icona Lucide")
    is_active = models.BooleanField(default=True, verbose_name="Attivo")

    class Meta:
        verbose_name = "Ufficio"
        verbose_name_plural = "Uffici"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class UserProfile(models.Model):
    """Profilo utente esteso con ufficio di appartenenza"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    office = models.ForeignKey(Office, on_delete=models.PROTECT, related_name='members',
                               verbose_name="Ufficio")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefono")

    class Meta:
        verbose_name = "Profilo Utente"
        verbose_name_plural = "Profili Utenti"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.office.name}"


class OfficeFieldPermission(models.Model):
    """Permessi RBAC a livello di campo per ogni ufficio"""
    PERMISSION_CHOICES = [
        ('READ', 'Sola Lettura'),
        ('WRITE', 'Lettura e Scrittura'),
    ]

    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name='field_permissions',
                               verbose_name="Ufficio")
    model_name = models.CharField(max_length=50, verbose_name="Modello")
    field_name = models.CharField(max_length=50, verbose_name="Campo")
    permission_type = models.CharField(max_length=5, choices=PERMISSION_CHOICES,
                                       verbose_name="Tipo Permesso")

    class Meta:
        verbose_name = "Permesso Campo"
        verbose_name_plural = "Permessi Campi"
        unique_together = ('office', 'model_name', 'field_name')
        ordering = ['office', 'model_name', 'field_name']

    def __str__(self):
        return f"{self.office.code} | {self.model_name}.{self.field_name} → {self.permission_type}"
