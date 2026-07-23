Questa applicazione permette il monitoraggio e la gestione in tempo reale di macchinari industriali tramite un'architettura software divisa tra un frontend dinamico (Single Page Application) e un solido backend basato su Django.

## ⚙️ Architettura e Flusso di Lavoro

Il sistema è progettato per garantire un'esperienza utente fluida e dati costantemente aggiornati. Ecco come si sviluppa il ciclo di vita dell'applicazione:

### 1. Il Primo Accesso: Caricamento e Autenticazione
* **Richiesta Iniziale:** La richiesta arriva al file di configurazione centrale (`config/urls.py`), che riconosce che l'utente sta cercando di accedere alla pagina web e lo reindirizza all'app frontend.
* **Caricamento della SPA (Single Page Application):** L'app frontend risponde inviando al browser un'unica pagina base (`index.html`) e i file statici associati (il foglio di stile `styles.css` e i file JavaScript). Da questo momento, l'interfaccia diventa dinamica e non ricarica più l'intera pagina web.
* **Controllo degli Accessi:** Lo script `auth.js` verifica se l'utente ha una sessione attiva. Se non è loggato, l'interfaccia mostra il modulo di login. Le credenziali inserite vengono inviate (tramite `api.js`) all'app accounts del backend.
* **Validazione Backend:** Le `views.py` e `serializers.py` di accounts interrogano il database (`db.sqlite3`) per verificare le credenziali e generano un "token" o una sessione sicura, gestita da `permissions.py` per definire cosa quell'utente può fare (es. utente uff.IT vs. utente uff.amministrazione).

### 2. Richiesta e Visualizzazione dei Dati dei Macchinari
Una volta che l'utente è autenticato, il sistema deve mostrargli lo stato della fabbrica o dei macchinari:
* **Inizializzazione della Dashboard:** Il file `app.js` avvia l'interfaccia principale e passa il controllo a `dashboard.js`. Questo script richiede i dati dei macchinari al backend usando `api.js`.
* **Interrogazione del Database (App Machines):** La richiesta API arriva alle rotte di `machines/urls.py` e viene elaborata dalle `views.py` dell'app machines. Se l'utente ha usato la barra di ricerca o dei filtri nel frontend, il file `filters.py` interviene per estrarre dal database solo le macchine rilevanti (es. "mostra solo le macchine in blocco").
* **Serializzazione dei Dati:** I dati estratti dal database (`models.py`) sono "grezzi". Il file `serializers.py` li converte in un pacchetto JSON ben formattato e li spedisce indietro al frontend.
* **Rendering (Costruzione Visiva):** Il file `dashboard.js` riceve i dati JSON e usa i moduli definiti in `components.js` (come tabelle, grafici o schede) per rappresentare i macchinari sullo schermo in tempo reale.

### 3. Il Cuore Industriale: La Simulazione del PLC
In un'applicazione reale, le macchine industriali comunicano i loro parametri tramite un PLC. Questo progetto include un motore di simulazione autonomo.
* **Generazione dei Dati:** In background, viene eseguito lo script `simulate_plc.py`. Questo file agisce come se fosse una fabbrica vera e propria: calcola temperature finte, genera variazioni di stato o simula errori per le varie macchine e li scrive continuamente nel database (`db.sqlite3`).
* **Aggiornamento dell'Interfaccia:** Il frontend (`dashboard.js`), tramite un meccanismo di aggiornamento ciclico, continua a richiedere i dati freschi all'app machines. Di conseguenza, l'utente vede i grafici e i numeri della dashboard cambiare in tempo reale, riflettendo il lavoro svolto dal simulatore PLC.

## 🔄 Sintesi del Flusso di Dati
1. **Simulatore PLC (`simulate_plc.py`)** genera dati in background e li salva in Database (`db.sqlite3`).
2. **Utente** apre il browser e carica Frontend (`app.js`, `dashboard.js`).
3. **Frontend (`api.js`)** fa richieste sicure tramite token al Backend (config + `machines/views.py`).
4. **Backend** recupera i dati dal database, li filtra (`filters.py`), li impacchetta (`serializers.py`) e li invia al Frontend.
5. **Frontend (`components.js`)** mostra i parametri delle macchine aggiornati all'utente.

## 🔐 Ruoli e Permessi (RBAC)
Le regole sono definite in `accounts/permissions.py` (controlla l'accesso) e `machines/management/commands/seed_data.py` (definisce i ruoli iniziali).

### 1. Superuser
* Può fare tutto.
* Accesso completo a tutti i modelli, documenti e campi.
* Bypass delle regole RBAC.

### 2. Ufficio Informatico (code='IT')
* **Machine:** Scrittura su `matricola`. Sola lettura su `capannone`, `anno_avviamento`, `stato`.
* **MachineITData:** Scrittura su `tipo_accentratore`, `indirizzo_ip`, `note_it`.
* **MachineStatusLog:** Lettura su `pezzi_buoni`, `fermi_macchina`, `orario_fermo`, `motivo_fermo`, `stato`.
* **Documenti:** Nessun permesso per `MachineDocument` (dati di seed) e `MachineAdminDocument`.
* **Cosa non può fare:** Modificare campi Machine/TechData diversi da quelli elencati, accedere a documenti amministrativi.

### 3. Ufficio Tecnico (code='TECH')
* **Machine:** Scrittura su `matricola`, `capannone`, `anno_avviamento`. Sola lettura su `stato`.
* **MachineITData:** Sola lettura su `indirizzo_ip`.
* **MachineTechData:** Scrittura su `descrizione_tecnica`, `marca`, `modello`, `anno_costruzione`, `note_tecniche`.
* **Documenti:** Lettura e scrittura su tutti i documenti tecnici (`MachineDocument`). Nessun accesso a `MachineAdminDocument`.
* **Cosa non può fare:** Modificare campi IT diversi da quelli permessi, accedere/scrivere documenti amministrativi.

### 4. Amministrazione (code='AMM')
* **Machine:** Sola lettura su `matricola`, `capannone`, `anno_avviamento`, `stato`.
* **Documenti (Tech):** Lettura su tutti i documenti tecnici (`MachineDocument`).
* **Documenti (Admin):** Lettura e scrittura su tutti i documenti amministrativi (`MachineAdminDocument`).
* **Cosa non può fare:** Modificare Machine oltre la lettura, modificare `MachineITData`, modificare `MachineTechData`, scrivere documenti tecnici.
