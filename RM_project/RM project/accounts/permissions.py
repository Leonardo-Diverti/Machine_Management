# Questo file contiene le regole di autorizzazione personalizzate per i permessi di campo.
from rest_framework.permissions import BasePermission


def get_user_office_code(user):
    """Restituisce il codice dell'ufficio dell'utente in maiuscolo, se presente."""
    if user.is_superuser:
        return None
    try:
        office = user.profile.office
        return office.code.upper() if office and office.code else None
    except Exception:
        return None


def can_access_document_model(user, model_name, action='read'):
    """Controlla accesso ai documenti in base all'ufficio dell'utente."""
    if user.is_superuser:
        return True

    office_code = get_user_office_code(user)
    if office_code == 'ADMIN':
        if model_name == 'MachineAdminDocument':
            return action in {'read', 'write'}
        if model_name == 'MachineDocument':
            return action == 'read'
    elif office_code == 'TECH':
        if model_name == 'MachineDocument':
            return action in {'read', 'write'}
        if model_name == 'MachineAdminDocument':
            return False

    if action == 'write':
        return can_write_field(user, model_name, '*')
    return can_read_field(user, model_name, '*')


class HasFieldPermission(BasePermission):
    """
    Custom permission: verifica che l'utente abbia il permesso
    sul campo specifico in base al suo ufficio.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Il superuser ha accesso completo
        if request.user.is_superuser:
            return True
        # Verifica che l'utente abbia un profilo associato a un ufficio
        try:
            profile = request.user.profile
            return profile.office is not None
        except Exception:
            return False


def get_user_field_permissions(user, model_name):
    """
    Restituisce un dizionario {field_name: permission_type}
    per un dato utente e modello.
    """
    if user.is_superuser:
        return {'__all__': 'WRITE'}

    try:
        office = user.profile.office
    except Exception:
        return {}

    from .models import OfficeFieldPermission
    perms = OfficeFieldPermission.objects.filter(
        office=office,
        model_name=model_name
    )
    return {p.field_name: p.permission_type for p in perms}


def can_write_field(user, model_name, field_name):
    """Verifica se l'utente può scrivere un campo specifico."""
    perms = get_user_field_permissions(user, model_name)
    if '__all__' in perms and perms['__all__'] == 'WRITE':
        return True
    if '*' in perms and perms['*'] == 'WRITE':
        return True
    return perms.get(field_name) == 'WRITE'


def can_read_field(user, model_name, field_name):
    """Verifica se l'utente può leggere un campo specifico."""
    perms = get_user_field_permissions(user, model_name)
    if '__all__' in perms:
        return True
    if '*' in perms:
        return True
    return field_name in perms
