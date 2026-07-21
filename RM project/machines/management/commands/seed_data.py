# Questo file popola il database con dati demo, utenti e permessi iniziali.
"""
Seed database con dati iniziali:
- 3 Uffici (IT, Tecnico, Amministrazione)
- 3 Utenti demo
- Permessi RBAC
- 10 Macchinari con dati IT e tecnici
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Office, UserProfile, OfficeFieldPermission
from machines.models import (Machine, MachineITData, MachineTechData,
                             MachineStatusLog)
import random
from django.utils import timezone


class Command(BaseCommand):
    help = 'Popola il database con dati iniziali demo'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Creazione dati iniziali...\n')

        # ==========================================
        # UFFICI
        # ==========================================
        it_office, _ = Office.objects.get_or_create(
            code='IT',
            defaults={
                'name': 'Ufficio Informatico',
                'description': 'Gestione infrastruttura IT, reti e accentratori macchinari.',
                'color': '#3B82F6',
                'icon': 'monitor',
            }
        )
        tech_office, _ = Office.objects.get_or_create(
            code='TECH',
            defaults={
                'name': 'Ufficio Tecnico',
                'description': 'Gestione tecnica macchinari, documentazione e collaudi.',
                'color': '#F59E0B',
                'icon': 'wrench',
            }
        )
        admin_office, _ = Office.objects.get_or_create(
            code='ADMIN',
            defaults={
                'name': 'Amministrazione',
                'description': 'Gestione fatture, bolle, ordini e pagamenti macchinari.',
                'color': '#10B981',
                'icon': 'file-text',
            }
        )
        self.stdout.write(self.style.SUCCESS('✅ Uffici creati'))

        # ==========================================
        # PERMESSI RBAC
        # ==========================================
        permissions_data = [
            # --- UFFICIO IT ---
            (it_office, 'Machine', 'matricola', 'WRITE'),
            (it_office, 'Machine', 'capannone', 'READ'),
            (it_office, 'Machine', 'anno_avviamento', 'READ'),
            (it_office, 'Machine', 'stato', 'READ'),
            (it_office, 'MachineITData', 'tipo_accentratore', 'WRITE'),
            (it_office, 'MachineITData', 'indirizzo_ip', 'WRITE'),
            (it_office, 'MachineITData', 'note_it', 'WRITE'),
            (it_office, 'MachineStatusLog', 'pezzi_buoni', 'READ'),
            (it_office, 'MachineStatusLog', 'fermi_macchina', 'READ'),
            (it_office, 'MachineStatusLog', 'orario_fermo', 'READ'),
            (it_office, 'MachineStatusLog', 'motivo_fermo', 'READ'),
            (it_office, 'MachineStatusLog', 'stato', 'READ'),
            # --- UFFICIO TECNICO ---
            (tech_office, 'Machine', 'matricola', 'WRITE'),
            (tech_office, 'Machine', 'capannone', 'WRITE'),
            (tech_office, 'Machine', 'anno_avviamento', 'WRITE'),
            (tech_office, 'Machine', 'stato', 'READ'),
            (tech_office, 'MachineITData', 'indirizzo_ip', 'READ'),
            (tech_office, 'MachineTechData', 'descrizione_tecnica', 'WRITE'),
            (tech_office, 'MachineTechData', 'marca', 'WRITE'),
            (tech_office, 'MachineTechData', 'modello', 'WRITE'),
            (tech_office, 'MachineTechData', 'anno_costruzione', 'WRITE'),
            (tech_office, 'MachineTechData', 'note_tecniche', 'WRITE'),
            (tech_office, 'MachineDocument', '*', 'WRITE'),
            # --- AMMINISTRAZIONE ---
            (admin_office, 'Machine', 'matricola', 'READ'),
            (admin_office, 'Machine', 'capannone', 'READ'),
            (admin_office, 'Machine', 'anno_avviamento', 'READ'),
            (admin_office, 'Machine', 'stato', 'READ'),
            (admin_office, 'MachineDocument', '*', 'READ'),
            (admin_office, 'MachineAdminDocument', '*', 'WRITE'),
        ]

        for office, model, field, perm_type in permissions_data:
            OfficeFieldPermission.objects.get_or_create(
                office=office,
                model_name=model,
                field_name=field,
                defaults={'permission_type': perm_type}
            )
        self.stdout.write(self.style.SUCCESS('✅ Permessi RBAC configurati'))

        # ==========================================
        # UTENTI DEMO
        # ==========================================
        demo_users = [
            ('admin_it', 'demo1234', 'Marco', 'Rossi', it_office),
            ('admin_tech', 'demo1234', 'Laura', 'Bianchi', tech_office),
            ('admin_amm', 'demo1234', 'Giuseppe', 'Verdi', admin_office),
        ]

        for username, password, first, last, office in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@azienda.local',
                    'is_active': True,
                }
            )
            if created:
                user.set_password(password)
                user.save()
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'office': office}
            )

        # Crea il superuser se non esiste
        if not User.objects.filter(is_superuser=True).exists():
            superuser = User.objects.create_superuser(
                username='superadmin',
                password='admin1234',
                email='admin@azienda.local',
                first_name='Super',
                last_name='Admin'
            )
            UserProfile.objects.get_or_create(
                user=superuser,
                defaults={'office': it_office}
            )

        self.stdout.write(self.style.SUCCESS('✅ Utenti demo creati'))

        # ==========================================
        # MACCHINARI DEMO
        # ==========================================
        machines_data = [
            ('CNC-001', 'Capannone A', 2018, 'attiva', 'PLC', '192.168.1.101', 'Fanuc', 'Robodrill α-D21MiB5'),
            ('CNC-002', 'Capannone A', 2019, 'attiva', 'PLC', '192.168.1.102', 'DMG Mori', 'NLX 2500'),
            ('TRN-001', 'Capannone A', 2017, 'attiva', 'IOX', '192.168.1.103', 'Mazak', 'Quick Turn 250'),
            ('PRE-001', 'Capannone B', 2020, 'attiva', 'RIO', '192.168.1.201', 'Schuler', 'MSD 400'),
            ('PRE-002', 'Capannone B', 2015, 'in_manutenzione', 'RIO', '192.168.1.202', 'Komatsu', 'H2F300'),
            ('SAL-001', 'Capannone B', 2021, 'attiva', 'PLC', '192.168.1.203', 'Trumpf', 'TruLaser 3030'),
            ('FRE-001', 'Capannone C', 2016, 'attiva', 'IOX', '192.168.1.301', 'Haas', 'VF-2SS'),
            ('FRE-002', 'Capannone C', 2022, 'attiva', 'PLC', '192.168.1.302', 'Hermle', 'C 400'),
            ('RET-001', 'Capannone C', 2014, 'ferma', 'IOX', '192.168.1.303', 'Studer', 'S33'),
            ('PIG-001', 'Capannone D', 2023, 'attiva', 'PLC', '192.168.1.401', 'Bystronic', 'ByStar Fiber 3015'),
        ]

        for matr, cap, anno, stato, acc, ip, marca, modello in machines_data:
            machine, created = Machine.objects.get_or_create(
                matricola=matr,
                defaults={
                    'capannone': cap,
                    'anno_avviamento': anno,
                    'stato': stato,
                }
            )

            MachineITData.objects.get_or_create(
                machine=machine,
                defaults={
                    'tipo_accentratore': acc,
                    'indirizzo_ip': ip,
                }
            )

            MachineTechData.objects.get_or_create(
                machine=machine,
                defaults={
                    'marca': marca,
                    'modello': modello,
                    'anno_costruzione': anno - random.randint(0, 2),
                    'descrizione_tecnica': f'Centro di lavoro {marca} {modello}',
                }
            )

            # Crea alcuni log di stato iniziali
            if created:
                base_pezzi = random.randint(1000, 50000)
                base_fermi = random.randint(0, 15)
                for i in range(5):
                    MachineStatusLog.objects.create(
                        machine=machine,
                        stato=stato,
                        pezzi_buoni=base_pezzi + (i * random.randint(10, 100)),
                        fermi_macchina=base_fermi,
                    )

        self.stdout.write(self.style.SUCCESS('✅ Macchinari demo creati'))
        self.stdout.write(self.style.SUCCESS('\n🎉 Database popolato con successo!'))
        self.stdout.write('\nUtenti disponibili:')
        self.stdout.write('  admin_it    / demo1234  → Ufficio Informatico')
        self.stdout.write('  admin_tech  / demo1234  → Ufficio Tecnico')
        self.stdout.write('  admin_amm   / demo1234  → Amministrazione')
        self.stdout.write('  superadmin  / admin1234 → Superuser')
