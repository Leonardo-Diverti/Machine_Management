# Walkthrough — MachineHub Gestionale Macchinari

## Panoramica

Web App gestionale per la gestione centralizzata dei macchinari aziendali, con sistema RBAC (Role-Based Access Control) che adatta l'interfaccia in base all'ufficio dell'utente.

**Stack**: Django 5.x + DRF + SimpleJWT + HTML/CSS/JS vanilla

---

## Struttura Progetto

```
RM project/
├── config/                     # Configurazione Django
│   ├── settings.py             # Settings con DRF, JWT, CORS, timezone IT
│   └── urls.py                 # Routing principale
├── accounts/                   # Autenticazione e RBAC
│   ├── models.py               # Office, UserProfile, OfficeFieldPermission
│   ├── permissions.py          # Custom RBAC permission classes
│   ├── serializers.py          # User/Profile/Office serializers
│   └── views.py                # Login JWT, profilo utente, logout
├── machines/                   # Gestione macchinari
│   ├── models.py               # Machine, ITData, TechData, Document, AdminDocument, StatusLog
│   ├── serializers.py          # Serializers con dati annidati
│   ├── filters.py              # django-filter per ricerca rapida
│   ├── views.py                # ViewSets CRUD con RBAC a livello di campo
│   └── management/commands/
│       ├── seed_data.py        # Popolamento dati iniziali
│       └── simulate_plc.py     # Simulatore PLC real-time
├── frontend/                   # Frontend SPA
│   ├── templates/frontend/
│   │   └── index.html          # Template HTML completo
│   └── static/
│       ├── css/styles.css      # Design system industriale dark
│       └── js/
│           ├── auth.js         # Gestione JWT + permessi client-side
│           ├── api.js          # Client API centralizzato
│           ├── components.js   # Componenti UI (badge, form, modali)
│           ├── dashboard.js    # Logica pagine e polling
│           └── app.js          # Entry point
└── db.sqlite3                  # Database SQLite
```

---

## Funzionalità Implementate

### Backend
- **Autenticazione JWT** con login username/password
- **RBAC granulare** a livello di campo tramite tabella `OfficeFieldPermission`
- **API REST** complete: CRUD macchinari, dati IT/tecnici, documenti, stato live
- **Upload documenti** tecnici e amministrativi con file storage
- **Simulatore PLC** che aggiorna automaticamente contapezzi e stato ogni 10 secondi
- **3 uffici configurati**: IT, Tecnico, Amministrazione

### Frontend
- **Login screen** con design glassmorphism
- **Dashboard** con stat cards animate e live preview
- **Tabella macchinari** con filtri per stato, capannone e ricerca libera
- **Dettaglio macchinario** modale con tab per Generale, Dati IT, Dati Tecnici, Documenti
- **Stato Live** con card real-time aggiornate via polling ogni 5 secondi
- **Form dinamici** che mostrano campi editabili/read-only in base al ruolo
- **Design responsivo** (desktop, tablet, mobile)
- **Toast notifications** per feedback operazioni

---

## Utenti Demo

| Username | Password | Ufficio | Permessi principali |
|---|---|---|---|
| `admin_it` | `demo1234` | Ufficio Informatico | Write: matricola, accentratore, IP. Read: stato, pezzi, fermi |
| `admin_tech` | `demo1234` | Ufficio Tecnico | Write: matricola, capannone, anno, dati tecnici, documenti tecnici |
| `admin_amm` | `demo1234` | Amministrazione | Write: documenti amministrativi (fatture, bolle, ordini). Read: dati base |
| `superadmin` | `admin1234` | Superuser | Accesso completo |

---

## Screenshot Test

### Login Page
![Login MachineHub](C:/Users/leona/.gemini/antigravity-ide/brain/eecd4a71-d048-4e54-bdaa-e2a18d42c699/login_page_1783017782407.png)

### Dashboard (Ufficio IT)
![Dashboard](C:/Users/leona/.gemini/antigravity-ide/brain/eecd4a71-d048-4e54-bdaa-e2a18d42c699/dashboard_clean_1783017804994.png)

### Tabella Macchinari
![Tabella Macchinari](C:/Users/leona/.gemini/antigravity-ide/brain/eecd4a71-d048-4e54-bdaa-e2a18d42c699/machines_list_1783017811875.png)

### Dettaglio Macchinario
![Dettaglio Macchinario](C:/Users/leona/.gemini/antigravity-ide/brain/eecd4a71-d048-4e54-bdaa-e2a18d42c699/machine_detail_modal_1783017817985.png)

### Stato Live
![Stato Live](C:/Users/leona/.gemini/antigravity-ide/brain/eecd4a71-d048-4e54-bdaa-e2a18d42c699/live_status_1783017827058.png)

---

## Come Avviare

```bash
# Avvia il server Django
python manage.py runserver 8000

# Avvia il simulatore PLC (in un altro terminale)
python manage.py simulate_plc --interval 10

# Apri nel browser
# http://localhost:8000
```

---

## Test Eseguiti

- ✅ Login con username/password (JWT)
- ✅ Dashboard con statistiche e live preview
- ✅ Tabella macchinari con filtri
- ✅ Dettaglio macchinario con tab
- ✅ Stato live con aggiornamento real-time
- ✅ RBAC: campi visibili/editabili corretti per ruolo IT
- ✅ Simulatore PLC funzionante con aggiornamento contapezzi
