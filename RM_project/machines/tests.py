from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Office, UserProfile
from .models import Machine, MachineDocument, MachineAdminDocument


class FiscalBenefitTests(TestCase):
    def setUp(self):
        self.office = Office.objects.create(name='Amministrazione', code='ADMIN', color='#2563EB')
        self.user = get_user_model().objects.create_user(username='adminuser', password='testpass')
        UserProfile.objects.create(user=self.user, office=self.office)
        self.machine = Machine.objects.create(
            cdl='CDL-TEST',
            cc='CC-TEST',
            capannone='Capannone 1',
            stato='attiva',
            interconnessione_stato='interconnessa',
        )
        from .models import MachineITData
        MachineITData.objects.create(
            machine=self.machine,
            tipo_accentratore='PLC'
        )

    def test_toggle_benefit_fiscal_creates_state(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

        response = self.client.get(f'/api/machines/{self.machine.id}/benefit_fiscal/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['attivo'])

        response = self.client.post(
            f'/api/machines/{self.machine.id}/benefit_fiscal/',
            {'attivo': True},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['attivo'])
        self.assertTrue(hasattr(self.machine, 'benefit_fiscal'))

    def test_cannot_edit_fiscal_fields_if_benefit_not_active(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        
        # Prova ad aggiornare i campi fiscali (beneficio non ancora attivo)
        response = self.client.patch(
            f'/api/machines/{self.machine.id}/',
            {'id_investimento_rm': '1234'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('I campi fiscali possono essere inseriti solo per macchine con beneficio fiscale attivato.', response.json()['error'])
        
        # Attiva il beneficio
        self.client.post(f'/api/machines/{self.machine.id}/benefit_fiscal/', {'attivo': True}, content_type='application/json')
        
        # Ora l'aggiornamento deve avere successo
        response = self.client.patch(
            f'/api/machines/{self.machine.id}/',
            {'id_investimento_rm': '1234'},
            content_type='application/json'
        )
        if response.status_code != 200:
            print("ERROR RESPONSE:", response.json())
        self.assertEqual(response.status_code, 200)
        self.machine.refresh_from_db()
        self.assertEqual(self.machine.id_investimento_rm, 1234)

    def test_other_user_from_same_office_cannot_delete_uploaded_document(self):
        tech_office = Office.objects.create(name='Tecnico', code='TECH', color='#F59E0B')
        uploader = get_user_model().objects.create_user(username='uploader', password='testpass')
        other_user = get_user_model().objects.create_user(username='otheruser', password='testpass')
        UserProfile.objects.create(user=uploader, office=tech_office)
        UserProfile.objects.create(user=other_user, office=tech_office)

        document = MachineDocument.objects.create(
            machine=self.machine,
            tipo_documento='ALTRO',
            nome_file='test.pdf',
            file=SimpleUploadedFile('test.pdf', b'file-content', content_type='application/pdf'),
            uploaded_by=uploader,
        )

        token = str(RefreshToken.for_user(other_user).access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

        response = self.client.delete(f'/api/machines/{self.machine.id}/documents/{document.id}/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(MachineDocument.objects.filter(pk=document.id).exists())

    def test_fiscal_benefit_documents_are_added_to_admin_document_collection(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'

        response = self.client.post(
            f'/api/machines/{self.machine.id}/benefit_fiscal_documents/',
            {
                'operation': 'fatture',
                'files': [SimpleUploadedFile('benefit.pdf', b'benefit-content', content_type='application/pdf')],
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(MachineAdminDocument.objects.filter(machine=self.machine).exists())

