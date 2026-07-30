# Questo file serializza i dati utente e il profilo per le API.
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Office, UserProfile, OfficeFieldPermission


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ['id', 'name', 'code', 'description', 'color', 'icon', 'is_active']


class OfficeFieldPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficeFieldPermission
        fields = ['id', 'model_name', 'field_name', 'permission_type']


class UserProfileSerializer(serializers.ModelSerializer):
    office = OfficeSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'phone', 'office', 'permissions']

    def get_permissions(self, obj):
        """Restituisce i permessi raggruppati per modello"""
        perms = OfficeFieldPermission.objects.filter(office=obj.office)
        result = {}
        for perm in perms:
            if perm.model_name not in result:
                result[perm.model_name] = {}
            result[perm.model_name][perm.field_name] = perm.permission_type
        return result


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile']
