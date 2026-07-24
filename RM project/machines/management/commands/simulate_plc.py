# Questo file simula l'arrivo di dati PLC e aggiorna gli stati dei macchinari.
"""
Simulatore PLC - Aggiorna automaticamente stati e contapezzi dei macchinari.

Simula i dati provenienti da accentratori IOX/RIO/PLC:
- Incremento progressivo del contapezzi buoni
- Cambi di stato casuali (attiva, ferma, in_manutenzione)
- Generazione eventi di fermo con motivi realistici

Uso: python manage.py simulate_plc
"""

import random
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from machines.models import Machine, MachineStatusLog


MOTIVI_FERMO = [
    'Guasto meccanico',
    'Guasto elettrico',
    'Manutenzione programmata',
    'Cambio utensile',
    'Mancanza materiale',
    'Pulizia programmata',
    'Regolazione parametri',
    'Cambio stampo',
    'Attesa qualità',
    'Guasto sensore',
]


class Command(BaseCommand):
    help = 'Simula dati PLC: aggiorna stati e contapezzi macchinari in tempo reale'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=10,
            help='Intervallo tra aggiornamenti in secondi (default: 10)'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(
            self.style.SUCCESS(f'Simulatore PLC avviato (intervallo: {interval}s)')
        )
        self.stdout.write('Premi Ctrl+C per fermare.\n')

        # Stato interno del contatore cumulativo
        counters = {}

        while True:
            try:
                machines = Machine.objects.exclude(
                    stato__in=['in_costruzione', 'dismessa']
                )

                if not machines.exists():
                    self.stdout.write(self.style.WARNING('Nessun macchinario attivo trovato.'))
                    time.sleep(interval)
                    continue

                for machine in machines:
                    # Inizializza i contatori se non sono presenti
                    if machine.id not in counters:
                        last_log = machine.status_logs.first()
                        counters[machine.id] = {
                            'pezzi': last_log.pezzi_buoni if last_log else 0,
                            'fermi': last_log.fermi_macchina if last_log else 0,
                        }

                    current_stato = machine.stato
                    new_stato = current_stato
                    motivo_fermo = None
                    orario_fermo = None

                    # Logica di transizione dello stato
                    if current_stato == 'attiva':
                        # Probabilità del 5% di fermo
                        if random.random() < 0.05:
                            new_stato = random.choice(['ferma', 'in_manutenzione'])
                            motivo_fermo = random.choice(MOTIVI_FERMO)
                            orario_fermo = timezone.now()
                            counters[machine.id]['fermi'] += 1
                        else:
                            # Incrementa il contatore dei pezzi (tra 5 e 50)
                            counters[machine.id]['pezzi'] += random.randint(5, 50)

                    elif current_stato == 'ferma':
                        # Probabilità del 20% di ripresa
                        if random.random() < 0.20:
                            new_stato = 'attiva'
                        else:
                            motivo_fermo = random.choice(MOTIVI_FERMO)
                            orario_fermo = timezone.now()

                    elif current_stato == 'in_manutenzione':
                        # Probabilità del 15% di tornare attiva
                        if random.random() < 0.15:
                            new_stato = 'attiva'
                        else:
                            motivo_fermo = 'Manutenzione in corso'
                            orario_fermo = timezone.now()

                    # Aggiorna lo stato della macchina
                    if new_stato != current_stato:
                        machine.stato = new_stato
                        machine.save(update_fields=['stato', 'updated_at'])

                    # Crea il log di stato
                    MachineStatusLog.objects.create(
                        machine=machine,
                        stato=new_stato,
                        pezzi_buoni=counters[machine.id]['pezzi'],
                        fermi_macchina=counters[machine.id]['fermi'],
                        orario_fermo=orario_fermo,
                        motivo_fermo=motivo_fermo,
                    )

                timestamp = timezone.now().strftime('%H:%M:%S')
                active_count = machines.filter(stato='attiva').count()
                self.stdout.write(
                    f'[{timestamp}] Aggiornate {machines.count()} macchine '
                    f'({active_count} attive)'
                )

                time.sleep(interval)

            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS('\nSimulatore PLC fermato.'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Errore: {e}'))
                time.sleep(interval)
