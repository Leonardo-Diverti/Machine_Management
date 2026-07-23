from django.core.management.base import BaseCommand
from machines.models import FaseCostruzione

class Command(BaseCommand):
    help = "Inizializza o aggiorna le fasi di costruzione master per macchine complesse e ad acquisto diretto"

    def handle(self, *args, **options):
        fasi = [
            # Ufficio Tecnico (TECH)
            {"ordine": 1, "nome": "creazione commesse", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 2, "nome": "inserimento macchina in database macchine", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 3, "nome": "entrata merci", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 4, "nome": "posizionamento macchina", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 5, "nome": "allacciamenti", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 6, "nome": "installazione HMI", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 7, "nome": "installazione EWON", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 8, "nome": "acquisizione scheda VDR", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            {"ordine": 9, "nome": "Verbale di collaudo", "ufficio": "TECH", "tipo": "ENTRAMBE"},
            
            # Ufficio IT
            {"ordine": 10, "nome": "installazione mikrotik", "ufficio": "IT", "tipo": "ENTRAMBE"},
            {"ordine": 11, "nome": "installazione raspberry-console", "ufficio": "IT", "tipo": "ENTRAMBE"},
            {"ordine": 12, "nome": "collegamento macchina-Niagara", "ufficio": "IT", "tipo": "ENTRAMBE"},
            {"ordine": 13, "nome": "allacciamento a MES", "ufficio": "IT", "tipo": "ENTRAMBE"},
        ]

        count_created = 0
        count_updated = 0

        for item in fasi:
            # Cerca le fasi esistenti ignorando maiuscole/minuscole per evitare conflitti
            existing = FaseCostruzione.objects.filter(
                nome__iexact=item["nome"],
                ufficio_competente=item["ufficio"]
            )

            if existing.exists():
                # Prende il primo record e lo aggiorna
                fase = existing.first()
                fase.nome = item["nome"]
                fase.ordine = item["ordine"]
                fase.tipo_macchina_applicabile = item["tipo"]
                fase.save()
                
                # Elimina eventuali duplicati ridondanti dello stesso tipo
                existing.exclude(id=fase.id).delete()
                count_updated += 1
            else:
                # Crea la fase se non esiste
                FaseCostruzione.objects.create(
                    nome=item["nome"],
                    ordine=item["ordine"],
                    ufficio_competente=item["ufficio"],
                    tipo_macchina_applicabile=item["tipo"]
                )
                count_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Inizializzazione completata! Nuove fasi create: {count_created}, Fasi aggiornate/pulite: {count_updated}."
            )
        )