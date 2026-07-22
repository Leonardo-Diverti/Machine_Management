// Questo file gestisce la logica della dashboard e delle interazioni utente.

/**
 * dashboard.js — Logica dashboard, pagine e interazioni
 */

const Dashboard = {
    pollingInterval: null,
    currentPage: 'dashboard',

    // === INIZIALIZZAZIONE ===
    async init() {
        this.setupUI();
        this.setupNavigation();
        this.setupEventListeners();
        await this.loadDashboard();
        this.startPolling();
    },

    setupUI() {
        const user = Auth.getUser();
        const office = Auth.getUserOffice();

        // Informazioni utente
        if (user) {
            const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username;
            document.getElementById('user-name').textContent = fullName;
            document.getElementById('user-avatar').textContent =
                (user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username[0].toUpperCase();
        }

        // Informazioni ufficio
        if (office) {
            document.getElementById('user-office').textContent = office.name;
            document.getElementById('office-badge-text').textContent = office.name;
            if (office.color) {
                document.getElementById('office-dot').style.background = office.color;
            }
        }

 // Mostra/nasconde il pulsante "Nuovo Macchinario"
        const toolbarActions = document.getElementById('toolbar-actions');
        
        if (Auth.isTechnicalOffice() || (Auth.getUser() && Auth.getUser().is_superuser)) {
            toolbarActions.innerHTML = `
                <button class="btn btn-primary btn-sm" onclick="Dashboard.showCreateForm()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Nuovo Macchinario
                </button>
            `;
        } else {
            // Rimuove esplicitamente il bottone per gli uffici non autorizzati
            toolbarActions.innerHTML = ''; 
        }
    },

    // === NAVIGAZIONE ===
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });

        document.querySelectorAll('.card-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigateTo(page);
            });
        });
    },

    navigateTo(page) {
        // Aggiorna la navigazione
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const activeNav = document.querySelector(`[data-page="${page}"]`);
        if (activeNav) activeNav.classList.add('active');

        // Aggiorna le pagine
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const activePage = document.getElementById(`page-${page}`);
        if (activePage) activePage.classList.add('active');

        // Aggiorna il titolo
        const titles = {
            'dashboard': 'Dashboard',
            'machines': 'Macchinari',
            'live': 'Stato Live',
        };
        document.getElementById('page-title').textContent = titles[page] || page;

        this.currentPage = page;

        // Carica i dati della pagina
        if (page === 'machines') this.loadMachinesTable();
        if (page === 'live') this.loadLiveStatus();

        // Chiude la barra laterale mobile
        document.getElementById('sidebar').classList.remove('open');
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) overlay.classList.remove('active');
    },

    // === LISTENER DEGLI EVENTI ===
    setupEventListeners() {
        // Ricerca
        let searchTimeout;
        document.getElementById('search-input').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => this.loadMachinesTable(), 300);
        });

        // Filtri
        document.getElementById('filter-stato').addEventListener('change', () => this.loadMachinesTable());
        document.getElementById('filter-capannone').addEventListener('change', () => this.loadMachinesTable());

        // Chiusura della modale
        document.getElementById('modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('form-modal-close').addEventListener('click', () => this.closeFormModal());

        // Chiude le modali cliccando sull'overlay
        document.getElementById('machine-modal').addEventListener('click', (e) => {
            if (e.target.id === 'machine-modal') this.closeModal();
        });
        document.getElementById('form-modal').addEventListener('click', (e) => {
            if (e.target.id === 'form-modal') this.closeFormModal();
        });

        // Menu mobile
        document.getElementById('mobile-menu-btn').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
            let overlay = document.querySelector('.sidebar-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                document.body.appendChild(overlay);
                overlay.addEventListener('click', () => {
                    document.getElementById('sidebar').classList.remove('open');
                    overlay.classList.remove('active');
                });
            }
            overlay.classList.toggle('active');
        });

        // Cambio scheda nelle modali
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('tab-btn')) {
                const tabIndex = e.target.dataset.tab;
                const modal = e.target.closest('.modal');
                modal.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
                modal.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                e.target.classList.add('active');
                modal.querySelector(`[data-tab-content="${tabIndex}"]`).classList.add('active');
            }
        });

        // Tasto ESC per chiudere le modali
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
                this.closeFormModal();
            }
        });
    },

    // === CARICAMENTO DASHBOARD ===
    async loadDashboard() {
        try {
            const stats = await API.getMachineStats();
            this.animateNumber('stat-total', stats.totale);
            this.animateNumber('stat-active', stats.attive);
            this.animateNumber('stat-stopped', stats.ferme);
            this.animateNumber('stat-maintenance', stats.in_manutenzione);

            // Macchinari recenti
            const machinesData = await API.getMachines({ page_size: 5 });
            const machines = machinesData.results || machinesData;
            this.renderRecentMachines(machines);

            // Anteprima live
            const liveData = await API.getLiveStatus();
            this.renderLivePreview(liveData);

            // Popola il filtro del capannone
            this.populateCapannoneFilter(machines);

        } catch (err) {
            console.error('Dashboard load error:', err);
        }
    },

    animateNumber(elementId, target) {
        const el = document.getElementById(elementId);
        const current = parseInt(el.textContent) || 0;
        const duration = 600;
        const start = performance.now();

        const animate = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(current + (target - current) * eased);
            if (progress < 1) requestAnimationFrame(animate);
        };

        requestAnimationFrame(animate);
    },

    renderRecentMachines(machines) {
        const container = document.getElementById('recent-machines');
        if (!machines || machines.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nessun macchinario trovato.</p></div>';
            return;
        }
        container.innerHTML = machines.slice(0, 6).map(m => `
            <div class="mini-machine-item" onclick="Dashboard.showMachineDetail(${m.id})">
                <div class="mini-machine-info">
                    ${Components.statusBadge(m.stato)}
                    <span class="mini-machine-matricola">${m.cdl || ''} - ${m.cc || ''}</span>
                </div>
                <span class="mini-machine-capannone">${m.capannone}</span>
            </div>
        `).join('');
    },

    renderLivePreview(data) {
        const container = document.getElementById('live-preview');
        if (!data || data.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>Nessun dato live.</p></div>';
            return;
        }
        container.innerHTML = data.slice(0, 12).map(m => {
            const dotColor = m.stato === 'attiva' ? 'var(--color-active)' :
                             m.stato === 'ferma' ? 'var(--color-stopped)' : 'var(--color-maintenance)';
            return `
                <div class="live-mini-card">
                    <span class="status-dot" style="background:${dotColor};"></span>
                    <span class="matricola">${m.cdl || ''} ${m.cc || ''}</span>
                    <span class="pezzi">${Components.formatNumber(m.pezzi_buoni)} pz</span>
                </div>
            `;
        }).join('');
    },

    // === TABELLA MACCHINARI ===
    async loadMachinesTable() {
        const tbody = document.getElementById('machines-tbody');
        tbody.innerHTML = '<tr><td colspan="7" class="loading-placeholder">Caricamento...</td></tr>';

        try {
            const params = {};
            const search = document.getElementById('search-input').value;
            const stato = document.getElementById('filter-stato').value;
            const capannone = document.getElementById('filter-capannone').value;

            if (search) params.search = search;
            if (stato) params.stato = stato;
            if (capannone) params.capannone = capannone;

            const data = await API.getMachines(params);
            const machines = data.results || data;

            if (!machines || machines.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="loading-placeholder">Nessun macchinario trovato.</td></tr>';
                return;
            }

            tbody.innerHTML = machines.map(m => {
                const ls = m.latest_status;
                const showPezzi = Auth.hasAnyPermission('MachineStatusLog');
                return `
                    <tr>
                        <td><strong>${m.cdl || '-'}</strong></td>
                        <td><strong>${m.cc || '-'}</strong></td>
                        <td>${m.capannone}</td>
                        <td>${m.anno_avviamento || '—'}</td>
                        <td>${Components.statusBadge(m.stato)}</td>
                        <td class="col-pezzi">${showPezzi && ls ? Components.formatNumber(ls.pezzi_buoni) : '—'}</td>
                        <td>
                            <div class="table-actions">
                                <button class="btn-icon" title="Dettaglio" onclick="Dashboard.showMachineDetail(${m.id})">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');

            this.populateCapannoneFilter(machines);

        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="7" class="loading-placeholder">Errore: ${err.message}</td></tr>`;
        }
    },

    populateCapannoneFilter(machines) {
        const select = document.getElementById('filter-capannone');
        const currentValue = select.value;
        const capannoni = [...new Set(machines.map(m => m.capannone))].sort();

        // Aggiorna solo se le opzioni sono cambiate
        const existingOptions = Array.from(select.options).slice(1).map(o => o.value);
        if (JSON.stringify(capannoni) !== JSON.stringify(existingOptions)) {
            select.innerHTML = '<option value="">Tutti i capannoni</option>' +
                capannoni.map(c => `<option value="${c}" ${c === currentValue ? 'selected' : ''}>${c}</option>`).join('');
        }
    },

    // === STATO LIVE ===
    async loadLiveStatus() {
        const container = document.getElementById('live-grid');

        try {
            const data = await API.getLiveStatus();

            if (!data || data.length === 0) {
                container.innerHTML = '<div class="empty-state"><p>Nessun macchinario attivo.</p></div>';
                return;
            }

            container.innerHTML = data.map(m => `
                <div class="live-card live-card--${m.stato}" onclick="Dashboard.showMachineDetail(${m.id})">
                    <div class="live-card-header">
                        <span class="live-card-title">${m.cdl || ''} / ${m.cc || ''}</span>
                        ${Components.statusBadge(m.stato)}
                    </div>
                    <div class="live-card-body">
                        <div class="live-stat">
                            <span class="live-stat-label">Pezzi Buoni</span>
                            <span class="live-stat-value pezzi">${Components.formatNumber(m.pezzi_buoni)}</span>
                        </div>
                        <div class="live-stat">
                            <span class="live-stat-label">Fermi</span>
                            <span class="live-stat-value fermi">${Components.formatNumber(m.fermi_macchina)}</span>
                        </div>
                        <div class="live-stat">
                            <span class="live-stat-label">Capannone</span>
                            <span class="live-stat-value">${m.capannone}</span>
                        </div>
                        <div class="live-stat">
                            <span class="live-stat-label">Ultimo Update</span>
                            <span class="live-stat-value">${m.last_update ? Components.formatTime(m.last_update) : '—'}</span>
                        </div>
                    </div>
                    ${m.motivo_fermo ? `
                        <div class="live-card-footer">
                            <div class="live-motivo">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                                ${m.motivo_fermo}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `).join('');

        } catch (err) {
            container.innerHTML = `<div class="empty-state"><p>Errore: ${err.message}</p></div>`;
        }
    },

    // === POLLING ===
    startPolling() {
        this.pollingInterval = setInterval(async () => {
            try {
                if (this.currentPage === 'dashboard') {
                    const stats = await API.getMachineStats();
                    this.animateNumber('stat-total', stats.totale);
                    this.animateNumber('stat-active', stats.attive);
                    this.animateNumber('stat-stopped', stats.ferme);
                    this.animateNumber('stat-maintenance', stats.in_manutenzione);

                    // Aggiunta: Aggiorna anche i macchinari recenti in tempo reale
                    const machinesData = await API.getMachines({ page_size: 5 });
                    const machines = machinesData.results || machinesData;
                    this.renderRecentMachines(machines);

                    const liveData = await API.getLiveStatus();
                    this.renderLivePreview(liveData);
                }

                if (this.currentPage === 'live') {
                    this.loadLiveStatus();
                }
            } catch (err) {
                console.warn('Polling error:', err);
            }
        }, 5000);
    },

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    },

    // === MODALE DETTAGLIO MACCHINARIO ===
    async showMachineDetail(id) {
        const modal = document.getElementById('machine-modal');
        const body = document.getElementById('modal-body');
        const title = document.getElementById('modal-title');

        body.innerHTML = '<div class="loading-placeholder">Caricamento dettaglio...</div>';
        modal.style.display = 'flex';

        try {
            const machine = await API.getMachine(id);
            title.textContent = `CDL: ${machine.cdl || '-'} | CC: ${machine.cc || '-'} - ${machine.capannone}`;
            body.innerHTML = Components.renderMachineDetail(machine);
        } catch (err) {
            body.innerHTML = `<div class="empty-state"><p>Errore: ${err.message}</p></div>`;
        }
    },

    closeModal() {
        document.getElementById('machine-modal').style.display = 'none';
    },

    // === MODALI FORM ===
    showCreateForm() {
        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');

        title.textContent = 'Nuovo Macchinario';
        body.innerHTML = Components.renderCreateForm();
        modal.style.display = 'flex';

        // Invio del form
        document.getElementById('create-machine-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            // Pulisce i valori vuoti
            if (!data.anno_avviamento) delete data.anno_avviamento;
            else data.anno_avviamento = parseInt(data.anno_avviamento);

            try {
                await API.createMachine(data);
                Components.toast('Macchinario creato con successo!', 'success');
                this.closeFormModal();
                this.loadMachinesTable();
                this.loadDashboard();
            } catch (err) {
                Components.toast(err.message, 'error');
            }
        });
    },

    async showEditForm(machineId) {
        this.closeModal();

        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');

        body.innerHTML = '<div class="loading-placeholder">Caricamento...</div>';
        modal.style.display = 'flex';

        try {
            const machine = await API.getMachine(machineId);
            title.textContent = `Modifica ${machine.cdl || ''} - ${machine.cc || ''}`;
            body.innerHTML = Components.renderEditForm(machine);

            // Invio del form
            document.getElementById('edit-machine-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData.entries());
                const id = data.machine_id;
                delete data.machine_id;

                try {
                    // Aggiorna i dati base del macchinario
                    const machineData = {};
                    if (Auth.canWrite('Machine', 'cdl') && data.cdl !== undefined) machineData.cdl = data.cdl;
                    if (Auth.canWrite('Machine', 'cc') && data.cc !== undefined) machineData.cc = data.cc;
                    if (Auth.canWrite('Machine', 'capannone') && data.capannone) machineData.capannone = data.capannone;
                    if (Auth.canWrite('Machine', 'anno_avviamento')) {
                        machineData.anno_avviamento = data.anno_avviamento ? parseInt(data.anno_avviamento) : null;
                    }

                    if (Object.keys(machineData).length > 0) {
                        await API.updateMachine(id, machineData);
                    }

                    // Aggiorna i dati IT
                    const itData = {};
                    if (Auth.canWrite('MachineITData', 'tipo_accentratore') && data.tipo_accentratore !== undefined) {
                        itData.tipo_accentratore = data.tipo_accentratore || null;
                    }
                    if (Auth.canWrite('MachineITData', 'indirizzo_ip') && data.indirizzo_ip !== undefined) {
                        itData.indirizzo_ip = data.indirizzo_ip || null;
                    }
                    if (Auth.canWrite('MachineITData', 'note_it') && data.note_it !== undefined) {
                        itData.note_it = data.note_it || '';
                    }

                    if (Object.keys(itData).length > 0) {
                        await API.updateITData(id, itData);
                    }

                    // Aggiorna i dati tecnici
                    const techData = {};
                    ['marca', 'modello', 'descrizione_tecnica', 'note_tecniche'].forEach(f => {
                        if (Auth.canWrite('MachineTechData', f) && data[f] !== undefined) {
                            techData[f] = data[f] || '';
                        }
                    });
                    if (Auth.canWrite('MachineTechData', 'anno_costruzione') && data.anno_costruzione !== undefined) {
                        techData.anno_costruzione = data.anno_costruzione ? parseInt(data.anno_costruzione) : null;
                    }

                    if (Object.keys(techData).length > 0) {
                        await API.updateTechData(id, techData);
                    }

                    Components.toast('Dati aggiornati con successo!', 'success');
                    this.closeFormModal();
                    this.loadMachinesTable();
                    this.loadDashboard();
                } catch (err) {
                    Components.toast(err.message, 'error');
                }
            });
        } catch (err) {
            body.innerHTML = `<div class="empty-state"><p>Errore: ${err.message}</p></div>`;
        }
    },

    showUploadForm(machineId, type) {
        this.closeModal();

        if (!Auth.canUploadDocumentType(type)) {
            Components.toast('Non hai i permessi per caricare questo tipo di documento.', 'error');
            return;
        }

        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');

        const titleText = type === 'admin' ? 'Carica Documento Amministrativo' : 'Carica Documento Tecnico';
        title.textContent = titleText;
        body.innerHTML = Components.renderUploadForm(machineId, type);
        modal.style.display = 'flex';

        // Invio del form
        document.getElementById('upload-doc-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const machId = formData.get('machine_id');
            const docType = formData.get('doc_type');
            formData.delete('machine_id');
            formData.delete('doc_type');

            try {
                if (docType === 'admin') {
                    await API.uploadAdminDocument(machId, formData);
                } else {
                    await API.uploadDocument(machId, formData);
                }
                Components.toast('Documento caricato con successo!', 'success');
                this.closeFormModal();
                this.showMachineDetail(machId);
            } catch (err) {
                Components.toast(err.message, 'error');
            }
        });
    },

    closeFormModal() {
        document.getElementById('form-modal').style.display = 'none';
    },
};
