# Questo file contiene una verifica manuale dei permessi di upload e accesso per i documenti tecnici e amministrativi del progetto.
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Office, OfficeFieldPermission, UserProfile
from machines.models import Machine


class DocumentPermissionChecks(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.machine = Machine.objects.create(matricola='M-001', capannone='Capannone A')

        self.admin_office = Office.objects.create(code='ADMIN', name='Amministrazione')
        self.tech_office = Office.objects.create(code='TECH', name='Ufficio Tecnico')

        self.admin_user = User.objects.create_user(username='admin_user', password='secret123')
        self.tech_user = User.objects.create_user(username='tech_user', password='secret123')

        UserProfile.objects.create(user=self.admin_user, office=self.admin_office)
        UserProfile.objects.create(user=self.tech_user, office=self.tech_office)

        OfficeFieldPermission.objects.create(
            office=self.admin_office,
            model_name='MachineDocument',
            field_name='*',
            permission_type='WRITE',
        )
        OfficeFieldPermission.objects.create(
            office=self.admin_office,
            model_name='MachineAdminDocument',
            field_name='*',
            permission_type='WRITE',
        )
        OfficeFieldPermission.objects.create(
            office=self.tech_office,
            model_name='MachineDocument',
            field_name='*',
            permission_type='WRITE',
        )
        OfficeFieldPermission.objects.create(
            office=self.tech_office,
            model_name='MachineAdminDocument',
            field_name='*',
            permission_type='WRITE',
        )

    def check_admin_cannot_upload_technical_documents(self):
        self.client.force_authenticate(self.admin_user)
        upload = SimpleUploadedFile(
            'manuale.pdf',
            b'pdf-content',
            content_type='application/pdf',
        )
        response = self.client.post(
            reverse('machine-documents', kwargs={'machine_id': self.machine.id}),
            {
                'tipo_documento': 'USO_MANUTENZIONE',
                'file': upload,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 403)

    def check_tech_office_cannot_access_admin_documents(self):
        self.client.force_authenticate(self.tech_user)
        response = self.client.get(
            reverse('machine-admin-documents', kwargs={'machine_id': self.machine.id})
        )

        self.assertEqual(response.status_code, 403)
