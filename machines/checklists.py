"""Definizioni delle checklist create quando nasce un macchinario."""

CHECKLISTS = {
    'COMPLESSA': {
        'TECH': [
            ('creazione_commesse', 'Creazione commesse'),
            ('inserimento_database', 'Inserimento macchina in database macchine'),
            ('entrata_merci', 'Entrata merci', ['BOLLA_TRASPORTO']),
            ('assemblaggio_macchina', 'Assemblaggio macchina',
             ['USO_MANUTENZIONE', 'CERTIFICAZIONE_CE']),
            ('allacciamenti', 'Allacciamenti'),
            ('installazione_plc', 'Installazione PLC'),
            ('installazione_hmi', 'Installazione HMI'),
            ('installazione_ewon', 'Installazione EWON'),
            ('installazione_robot', 'Installazione robot'),
            ('certificazione_ce', 'Certificazione CE', ['CERTIFICAZIONE_CE']),
            ('manuale_uso_manutenzione', 'Manuale di uso e manutenzione',
             ['USO_MANUTENZIONE']),
            ('acquisizione_scheda_vdr', 'Acquisizione scheda VDR', ['SCHEDA_VDR']),
            ('verbale_collaudo', 'Verbale di collaudo', ['VERBALE_COLLAUDO']),
        ],
        'IT': [
            ('installazione_mikrotik', 'Installazione Mikrotik'),
            ('installazione_raspberry_console', 'Installazione Raspberry-console'),
            ('allacciamento_mes', 'Allacciamento a MES'),
        ],
    },
    'ACQUISTO_DIRETTO': {
        'TECH': [
            ('creazione_commesse', 'Creazione commesse'),
            ('inserimento_database', 'Inserimento macchina in database macchine'),
            ('entrata_merci', 'Entrata merci', ['BOLLA_TRASPORTO']),
            ('posizionamento_macchina', 'Posizionamento macchina',
             ['USO_MANUTENZIONE', 'CERTIFICAZIONE_CE']),
            ('allacciamenti', 'Allacciamenti'),
            ('installazione_hmi', 'Installazione HMI'),
            ('installazione_ewon', 'Installazione EWON'),
            ('acquisizione_scheda_vdr', 'Acquisizione scheda VDR', ['SCHEDA_VDR']),
            ('verbale_collaudo', 'Verbale di collaudo', ['VERBALE_COLLAUDO']),
        ],
        'IT': [
            ('installazione_mikrotik', 'Installazione Mikrotik'),
            ('installazione_raspberry_console', 'Installazione Raspberry-console'),
            ('allacciamento_mes', 'Allacciamento a MES'),
        ],
    },
}


def create_checklist_for_machine(machine):
    """Crea le attivita' previste per il tipo della macchina."""
    from .models import MachineChecklistItem

    for office, items in CHECKLISTS[machine.tipo_macchina].items():
        for order, item in enumerate(items):
            code, label, *options = item
            document_types = options[0] if options else []
            read_only_tech = options[1] if len(options) > 1 else False
            MachineChecklistItem.objects.get_or_create(
                machine=machine,
                codice=code,
                defaults={
                    'descrizione': label,
                    'ufficio': office,
                    'ordine': order,
                    'document_types': document_types,
                    'solo_visualizzazione_tech': read_only_tech,
                },
            )