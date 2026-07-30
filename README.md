# RM Project — Gestionale Macchinari Industriali

Dashboard web per la gestione dell'intero ciclo di vita dei macchinari industriali: dall'avviamento alla produzione, con tracciamento in tempo reale dello stato, gestione documentale e controllo accessi basato su ruoli (RBAC).

---

## Indice

- [Panoramica](#panoramica)
- [Stack Tecnologico](#stack-tecnologico)
- [Architettura del Progetto](#architettura-del-progetto)
- [Modelli Dati](#modelli-dati)
- [Sistema di Permessi (RBAC)](#sistema-di-permessi-rbac)
- [Vincoli Operativi e Workflow](#vincoli-operativi-e-workflow)
- [API REST](#api-rest)
- [Frontend](#frontend)
- [Comandi di Gestione](#comandi-di-gestione)
- [Installazione e Avvio](#installazione-e-avvio)
- [Utenti Demo](#utenti-demo)

---

## Panoramica

Il sistema consente di:

- **Registrare macchinari** con anagrafica completa (CDL, CC, capannone, commesse, tipo macchina). Il capannone "Tubificio" è sempre disponibile di default, oltre a quelli generati dinamicamente.
- **Tracciare il ciclo di vita** dalla costruzione alla dismissione, passando per la messa in produzione.
- **Gestire checklist di avviamento** differenziate per tipo di macchina (complessa / acquisto diretto).
- **Caricare e organizzare documenti** tecnici e amministrativi con permessi restrittivi per ufficio.
- **Monitorare lo stato in tempo reale** dei macchinari (ad es. per monitorarne l'avanzamento verso l'interconnessione).
- **Gestire il beneficio fiscale** tramite procedure rigide per la validazione incrociata tra ufficio Tecnico, IT e Amministrazione, supportate da sincronizzazione automatica dei documenti.

---

## Stack Tecnologico

| Componente     | Tecnologia                          |
|----------------|-------------------------------------|
| Backend        | Django 4.2+                         |
| API            | Django REST Framework               |
| Autenticazione | JWT (Simple JWT)                    |
| Filtri         | django-filter                       |
| CORS           | django-cors-headers                 |
| Database       | SQLite (sviluppo)                   |
| Frontend       | HTML/CSS/JS vanilla (SPA)           |

---

## Architettura del Progetto

```text
RM project/
├── config/                  # Configurazione Django
├── accounts/                # App autenticazione e profili utente
│   ├── models.py            # Office, UserProfile, OfficeFieldPermission
│   └── ...
├── machines/                # App principale macchinari
│   ├── models.py            # Tutti i modelli (Machine, ITData, TechData, Documents, ecc.)
│   ├── views.py             # ViewSet e API per macchinari, documenti, checklist, benefit
│   ├── checklists.py        # Definizione checklist per tipo macchina
│   ├── management/commands/
│   │   ├── seed_data.py     # Comando per popolare il DB con dati demo
│   │   └── simulate_plc.py  # Simulatore dati PLC in tempo reale
│   └── ...
├── frontend/                # App frontend SPA
│   ├── static/
│   │   ├── css/styles.css   # Stili della dashboard
│   │   └── js/
│   │       ├── app.js       # Entry point e routing SPA
│   │       ├── api.js       # Client HTTP per le API
│   │       ├── auth.js      # Gestione autenticazione JWT
│   │       ├── components.js # Componenti UI riutilizzabili
│   │       └── dashboard.js  # Logica dashboard e viste
│   └── templates/frontend/
│       └── index.html       # Template HTML principale
├── media/documents/         # File caricati dagli utenti
├── manage.py                # Entry point Django
├── requirements.txt         # Dipendenze Python
└── db.sqlite3               # Database SQLite
```

---

## Modelli Dati

I modelli sono divisi tra l'app `accounts` (gestione degli uffici e utenti) e `machines` (anagrafica, dati tecnici, dati IT, documenti vari, iter checklist e log di stato).

### Ciclo di Vita del Macchinario

```text
in_costruzione → attiva → ferma / in_manutenzione
       │                                │
       └── Checklist completata ────────┘
           (tutte le attività + documenti richiesti)
```

Quando **tutte le voci della checklist** sono completate (inclusi i documenti obbligatori), il macchinario passa automaticamente allo stato **attiva**. Per favorire il coordinamento, la **data prevista per l'interconnessione** è visibile a tutti gli uffici direttamente nella scheda anagrafica generale.

### Tipi di Macchina e Checklist

Il sistema genera automaticamente le checklist in base al tipo di macchina:

**Macchina complessa** — 16 attività tra Ufficio Tecnico e IT:
- Creazione commesse, entrata merci, assemblaggio, allacciamenti. *Nota*: L'assemblaggio macchina non richiede obbligatoriamente il caricamento di manuali.
- Installazione PLC/HMI/EWON/Robot.
- Certificazione CE, manuali, scheda VDR, verbale di collaudo.
- Operazioni IT (Mikrotik, Raspberry, allacciamento MES).

**Macchina ad acquisto diretto** — 10 attività:
- Processi più brevi focalizzati su posizionamento e allacciamenti.

---

## Sistema di Permessi (RBAC)

Il sistema implementa un controllo accessi **a livello di campo** basato sull'ufficio di appartenenza dell'utente (IT, Tecnico, Amministrazione). 

- **Anagrafica base**: Solo Uff. Tecnico ha in scrittura, gli altri in lettura.
- **Dati IT / Dati Tecnici**: I rispettivi uffici hanno privilegi di scrittura, preclusi agli altri.
- **Amministrazione**: Può gestire i documenti amministrativi e la pratica del Beneficio Fiscale.

---

## Vincoli Operativi e Workflow

Il sistema applica regole stringenti (vincoli) per garantire la coerenza formale dei dati inseriti, specialmente per la pratica del **Beneficio Fiscale**:

1. **Requisiti per attivare il Beneficio Fiscale**:
   - L'Amministrazione **non può attivare** una pratica di Beneficio Fiscale finché la macchina non risulta **completamente interconnessa** (ovvero tutte le voci della checklist Tech/IT sono state completate).
   - È obbligatorio che l'ufficio IT abbia specificato **"PLC"** come *Tipo Accentratore* all'interno dei Dati IT. Se queste due condizioni non sono vere, il bottone di avvio pratica rimane disabilitato.

2. **Dati Investimento e Consulente**:
   - I campi amministrativi "ID Investimento RM", "ID Investimento Consulente" e "Consulente" (presenti nella maschera "Modifica Dati" di pertinenza dell'Amministrazione) sono **bloccati e non compilabili** finché la pratica del Beneficio Fiscale non viene ufficialmente "attivata".

3. **Sincronizzazione Automatica Documenti Tecnici/Amministrativi**:
   - L'ufficio Tecnico carica spesso documenti che servono anche all'Amministrazione (es. **Ordine di Acquisto** e **Documento di Trasporto**). 
   - Quando l'Ufficio Tecnico inserisce un "Ordine di Acquisto" o una "Bolla di Trasporto", il sistema **sincronizza automaticamente** questi documenti all'interno del pannello "Beneficio Fiscale".
   - L'Amministrazione li visualizzerà pronti per il download nell'apposita sezione contrassegnati dall'etichetta verde **Tech**, senza il rischio di fastidiose duplicazioni a database.

---

## API REST

Base URL: `/api/`

Espone endpoint completi per l'autenticazione (`/api/auth/login/`, ecc.) e la gestione a 360° dei macchinari (`/api/machines/`). Gli endpoint sono protetti, e un sofisticato filtro RBAC respinge le richieste se l'utente non dispone dei permessi appropriati a livello di campo.

---

## Comandi di Gestione

### `seed_data` — Popola il database con dati demo
```bash
python manage.py seed_data --reset
```

### `simulate_plc` — Simulatore dati PLC
```bash
python manage.py simulate_plc --interval 10
```
Crea un ciclo che aggiorna i dispositivi hardware simulati modificandone temporaneamente lo stato.

---

## Installazione e Avvio

1. Clona il progetto e crea un venv (`python -m venv venv`)
2. `pip install -r requirements.txt`
3. `python manage.py migrate` e `python manage.py seed_data`
4. `python manage.py runserver` (disponibile su http://localhost:8000)

## Utenti Demo

| Username      | Password    | Ufficio              |
|---------------|-------------|----------------------|
| `admin_it`    | `demo1234`  | Ufficio Informatico  |
| `admin_tech`  | `demo1234`  | Ufficio Tecnico      |
| `admin_amm`   | `demo1234`  | Amministrazione      |
| `superadmin`  | `admin1234` | Superuser            |
