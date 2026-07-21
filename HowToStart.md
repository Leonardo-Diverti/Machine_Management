# 🚀 How to Start - Guida all'Avvio

Benvenuto! Segui questi passaggi per configurare, avviare il progetto **Machine Management** e far partire la simulazione industriale sulla tua macchina locale.

## 1. Configurazione Iniziale del Progetto

Assicurati di avere Python installato sul tuo sistema. Apri il tuo terminale e posizionati nella cartella principale del progetto (quella che contiene il file `manage.py`).

### A. Installazione delle Dipendenze
Se il progetto include un file `requirements.txt`, installa le librerie necessarie eseguendo:
```bash
pip install -r requirements.txt
```

### B. Creazione del Database
Genera le tabelle necessarie nel database SQLite eseguendo le migrazioni di Django:
```bash
python manage.py migrate
```

### C. Popolamento dei Dati (Seed)
Inizializza il database con i ruoli utente (IT, TECH, ADMIN), i permessi e i dati di base necessari per il funzionamento:
```bash
python manage.py seed_data
```

## 2. Avvio dell'Applicazione

Per far funzionare l'applicazione in tempo reale simulando un vero ambiente di fabbrica, dovrai tenere in esecuzione due processi separati. Ti serviranno **due finestre del terminale aperte**.

### Terminale 1: Il Server Web (Backend e Frontend)
In questo terminale avvieremo il server che risponde alle richieste web.
```bash
python manage.py runserver
```

### Terminale 2: Il Simulatore PLC (Generazione Dati)
In una nuova finestra del terminale (sempre all'interno della cartella del progetto), esegui lo script autonomo che genera il traffico dati dei macchinari:
```bash
python manage.py simulate_plc
```

## 3. Accesso e Utilizzo

Una volta che entrambi i processi sono in esecuzione senza errori:

1. Apri il tuo browser web (Chrome, Firefox, Safari, ecc.).
2. Vai all'indirizzo: `http://127.0.0.1:8000`
3. Verrai automaticamente reindirizzato alla pagina di login gestita dalla SPA.
4. Effettua l'accesso utilizzando uno degli account generati dallo script `seed_data` per esplorare le dashboard in base al ruolo assegnato (Superuser, IT, Tecnico, o Amministratore).
5. Vedrai i grafici e i parametri della dashboard aggiornarsi in tempo reale grazie al simulatore PLC!
