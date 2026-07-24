# Questo file registra i modelli amministrativi dell'app accounts.
from django.contrib import admin
from .models import Office, UserProfile, OfficeFieldPermission


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'office', 'phone')
    list_filter = ('office',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(OfficeFieldPermission)
class OfficeFieldPermissionAdmin(admin.ModelAdmin):
    list_display = ('office', 'model_name', 'field_name', 'permission_type')
    list_filter = ('office', 'model_name', 'permission_type')
    search_fields = ('field_name',)
