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
        };
        document.getElementById('page-title').textContent = titles[page] || page;

        this.currentPage = page;

        // Carica i dati della pagina
        if (page === 'machines') this.loadMachinesTable();

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
        const filters = [
            'filter-stato', 'filter-capannone', 'filter-stabilimento', 
            'filter-interconnessione', 'filter-id-rm', 'filter-id-consulente', 
            'filter-cdl', 'filter-cc', 'filter-consulente', 'filter-anno'
        ];
        filters.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener(el.tagName === 'SELECT' ? 'change' : 'input', (e) => {
                    if (el.tagName !== 'SELECT') {
                        clearTimeout(searchTimeout);
                        searchTimeout = setTimeout(() => this.loadMachinesTable(), 300);
                    } else {
                        this.loadMachinesTable();
                    }
                });
            }
        });

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

            // Macchinari per il riepilogo avanzamento
            const machinesData = await API.getMachines(); // fetch all or default limit
            const machines = machinesData.results || machinesData;
            this.renderDashboardMachines(machines);

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

    renderDashboardMachines(machines) {
        const tbody = document.getElementById('dashboard-tbody');
        if (!machines || machines.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nessun macchinario trovato.</td></tr>';
            return;
        }

        tbody.innerHTML = machines.map(m => {
            const progress = m.checklist_progress || { completed: 0, total: 0 };
            const percent = progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0;
            
            let benefitBadge = '<span style="color:#9ca3af;font-size:0.85em;">Non disponibile</span>';
            if (m.interconnessione_stato === 'interconnessa') {
                const attivo = m.fiscal_benefit && m.fiscal_benefit.attivo;
                const chiuso = m.fiscal_benefit && m.fiscal_benefit.chiuso;
                if (chiuso) {
                    benefitBadge = '<span class="status-badge" style="background:#f3f4f6;color:#4b5563;">Beneficio Chiuso</span>';
                } else {
                    benefitBadge = attivo 
                        ? '<span class="status-badge" style="background:#dcfce7;color:#16a34a;">Attivo</span>' 
                        : '<span class="status-badge" style="background:#fee2e2;color:#dc2626;">Non Attivo</span>';
                }
            }

            return `
                <tr style="cursor: pointer;" onclick="Dashboard.showMachineDetail(${m.id})">
                    <td>
                        <div style="font-weight: 600;">${m.id_investimento_rm || 'Non assegnato'}</div>
                        <div style="font-size: 0.85em; color: #6b7280;">${m.cdl || '-'} • ${m.cc || '-'}</div>
                    </td>
                    <td onclick="Dashboard.showChecklist(${m.id}); event.stopPropagation();" title="Clicca per gestire la checklist">
                        <div style="display: flex; align-items: center; gap: 0.75rem;">
                            <div style="flex: 1; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                                <div style="height: 100%; width: ${percent}%; background: var(--color-primary); border-radius: 4px;"></div>
                            </div>
                            <span style="font-size: 0.85em; color: #4b5563; white-space: nowrap;">${progress.completed} / ${progress.total} fasi</span>
                        </div>
                    </td>
                    <td>${Components.statusBadge(m.stato)}</td>
                    <td>${Components.interconnessioneBadge(m.interconnessione_stato, m.id)}</td>
                    <td>${benefitBadge}</td>
                </tr>
            `;
        }).join('');
    },

    // === TABELLA MACCHINARI ===
    async loadMachinesTable() {
        const tbody = document.getElementById('machines-tbody');
        tbody.innerHTML = '<tr><td colspan="10" class="loading-placeholder">Caricamento...</td></tr>';

        try {
            const params = {};
            
            // Applica filtri
            const search = document.getElementById('search-input').value;
            if (search) params.search = search;
            
            const mapping = {
                'stato': 'filter-stato',
                'capannone': 'filter-capannone',
                'stabilimento': 'filter-stabilimento',
                'interconnessione_stato': 'filter-interconnessione',
                'id_investimento_rm': 'filter-id-rm',
                'id_investimento_consulente': 'filter-id-consulente',
                'cdl': 'filter-cdl',
                'cc': 'filter-cc',
                'consulente': 'filter-consulente',
                'anno_avviamento': 'filter-anno'
            };
            
            for (const [key, id] of Object.entries(mapping)) {
                const el = document.getElementById(id);
                if (el && el.value) {
                    params[key] = el.value;
                }
            }

            const data = await API.getMachines(params);
            const machines = data.results || data;

            if (!machines || machines.length === 0) {
                tbody.innerHTML = '<tr><td colspan="10" class="loading-placeholder">Nessun macchinario trovato.</td></tr>';
                return;
            }

            tbody.innerHTML = machines.map(m => {
                return `
                    <tr>
                        <td><strong>${m.cdl || '-'}</strong></td>
                        <td><strong>${m.cc || '-'}</strong></td>
                        <td>${m.capannone}</td>
                        <td>${m.stabilimento || '—'}</td>
                        <td>${m.anno_avviamento || '—'}</td>
                        <td>${['inserimento_db', 'ordinata', 'in_costruzione'].includes(m.stato)
                            ? `<button class="status-button" onclick="Dashboard.showChecklist(${m.id})">${Components.statusBadge(m.stato)}</button>`
                            : Components.statusBadge(m.stato)}</td>
                        <td>${Components.interconnessioneBadge(m.interconnessione_stato, m.id)}</td>
                        <td>${m.id_investimento_rm || '—'}</td>
                        <td>${m.id_investimento_consulente || '—'}</td>
                        <td>${m.consulente || '—'}</td>
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
            tbody.innerHTML = `<tr><td colspan="10" class="loading-placeholder">Errore: ${err.message}</td></tr>`;
        }
    },

    populateCapannoneFilter(machines) {
        const select = document.getElementById('filter-capannone');
        if (!select) return;
        
        const currentValue = select.value;
        const capannoni = [...new Set([...machines.map(m => m.capannone), 'Tubificio'])].sort();

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
                            <span class="live-stat-label">Capannone</span>
                            <span class="live-stat-value">${m.capannone}</span>
                        </div>
                        <div class="live-stat">
                            <span class="live-stat-label">Ultimo Update</span>
                            <span class="live-stat-value">${m.last_update ? Components.formatTime(m.last_update) : '—'}</span>
                        </div>
                    </div>
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

    async showChecklist(machineId) {
        const modal = document.getElementById('machine-modal');
        const body = document.getElementById('modal-body');
        const title = document.getElementById('modal-title');
        body.innerHTML = '<div class="loading-placeholder">Caricamento checklist...</div>';
        modal.style.display = 'flex';

        try {
            const [machine, items] = await Promise.all([
                API.getMachine(machineId),
                API.getMachineChecklist(machineId),
            ]);
            title.textContent = `Checklist - CDL: ${machine.cdl || '-'} | CC: ${machine.cc || '-'}`;
            body.innerHTML = Components.renderChecklist(machine, items);
        } catch (err) {
            body.innerHTML = `<div class="empty-state"><p>Errore: ${err.message}</p></div>`;
        }
    },

    async toggleChecklistItem(machineId, itemId, completed) {
        try {
            await API.updateChecklistItem(machineId, itemId, { completata: completed });
            await this.showChecklist(machineId);
            this.loadMachinesTable();
            if (typeof this.loadDashboard === 'function') {
                this.loadDashboard();
            }
        } catch (err) {
            Components.toast(err.message, 'error');
            await this.showChecklist(machineId);
        }
    },

    closeModal() {
        document.getElementById('machine-modal').style.display = 'none';
    },

    async deleteMachine(machineId) {
        if (!Auth.isTechnicalOffice() && !Auth.getUser()?.is_superuser) {
            Components.toast('Solo l’Ufficio Tecnico può eliminare i macchinari.', 'error');
            return;
        }

        const confirmed = window.confirm(
            'Eliminare definitivamente questo macchinario e tutti i documenti associati?'
        );
        if (!confirmed) return;

        try {
            await API.deleteMachine(machineId);
            Components.toast('Macchinario eliminato con successo.', 'success');
            this.closeModal();
            this.loadMachinesTable();
            this.loadDashboard();
        } catch (err) {
            Components.toast(err.message, 'error');
        }
    },

    // === MODALI FORM ===
    async showCreateForm() {
        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');

        title.textContent = 'Nuovo Macchinario';
        body.innerHTML = '<div class="loading-placeholder">Caricamento località...</div>';
        modal.style.display = 'flex';

        let locations = [];
        try {
            locations = await API.getMachineLocations();
        } catch (err) {
            body.innerHTML = `<div class="empty-state"><p>Impossibile caricare le località: ${err.message}</p></div>`;
            return;
        }
        body.innerHTML = Components.renderCreateForm(locations);
        this.setupMachineOrderFields(document.getElementById('create-machine-form'));

        // Invio del form
        document.getElementById('create-machine-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            // Raccogli commesse multiple
            data.commessa = formData.getAll('commessa').map(v => v.trim()).filter(v => v);
            data.commessa_macchina = formData.getAll('commessa_macchina').map(v => v.trim()).filter(v => v);
            data.commessa_automazione = formData.getAll('commessa_automazione').map(v => v.trim()).filter(v => v);

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

    setupMachineOrderFields(form) {
        const typeInputs = form.querySelectorAll('input[name="tipo_macchina"]');
        const orderGroups = form.querySelectorAll('[data-machine-type]');

        const updateFields = () => {
            const selectedType = form.querySelector('input[name="tipo_macchina"]:checked')?.value;
            orderGroups.forEach(group => {
                const visible = group.dataset.machineType === selectedType;
                group.hidden = !visible;
                group.querySelectorAll('input').forEach(input => {
                    input.required = visible;
                    if (!visible) input.value = '';
                });
            });
        };

        typeInputs.forEach(input => input.addEventListener('change', updateFields));
        updateFields();
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
                    if (Auth.isAdministration() || Auth.getUser()?.is_superuser) {
                        if (data.id_investimento_rm !== undefined) machineData.id_investimento_rm = data.id_investimento_rm ? parseInt(data.id_investimento_rm) : null;
                        if (data.id_investimento_consulente !== undefined) machineData.id_investimento_consulente = data.id_investimento_consulente ? parseInt(data.id_investimento_consulente) : null;
                        if (data.consulente !== undefined) machineData.consulente = data.consulente || '';
                    }

                    if (Object.keys(machineData).length > 0) {
                        await API.updateMachine(id, machineData);
                    }

                    // Aggiorna i dati IT
                    const itData = {};
                    const isIT = Auth.isITOffice() || Auth.getUser()?.is_superuser;
                    if (isIT && data.tipo_accentratore !== undefined) {
                        itData.tipo_accentratore = data.tipo_accentratore || null;
                    }
                    if (isIT && data.indirizzo_ip !== undefined) {
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

                    // Aggiorna i campi fiscali (solo ADMIN)
                    if (Auth.isAdministration() || Auth.getUser()?.is_superuser) {
                        const fiscalData = {};
                        if (data.id_investimento_rm !== undefined) {
                            fiscalData.id_investimento_rm = data.id_investimento_rm ? parseInt(data.id_investimento_rm) : null;
                        }
                        if (data.id_investimento_consulente !== undefined) {
                            fiscalData.id_investimento_consulente = data.id_investimento_consulente ? parseInt(data.id_investimento_consulente) : null;
                        }
                        if (data.consulente !== undefined) {
                            fiscalData.consulente = data.consulente || '';
                        }
                        if (Object.keys(fiscalData).length > 0) {
                            await API.updateMachine(id, fiscalData);
                        }
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

    async toggleFiscalBenefit(machineId) {
        try {
            const benefit = await API.getFiscalBenefit(machineId);
            if (!benefit?.attivo) {
                await API.toggleFiscalBenefit(machineId, true);
                Components.toast('Beneficio fiscale attivato.', 'success');
            }
            await this.showFiscalBenefit(machineId);
        } catch (err) {
            Components.toast(err.message, 'error');
        }
    },

    async showFiscalBenefit(machineId) {
        const modal = document.getElementById('machine-modal');
        const body = document.getElementById('modal-body');
        const title = document.getElementById('modal-title');
        body.innerHTML = '<div class="loading-placeholder">Caricamento beneficio fiscale...</div>';
        modal.style.display = 'flex';

        try {
            const [machine, benefit] = await Promise.all([
                API.getMachine(machineId),
                API.getFiscalBenefit(machineId),
            ]);
            title.textContent = `Beneficio fiscale - ${machine.cdl || '-'} | ${machine.cc || '-'}`;
            body.innerHTML = this.renderFiscalBenefit(machine, benefit);
        } catch (err) {
            body.innerHTML = `<div class="empty-state"><p>Errore: ${err.message}</p></div>`;
        }
    },

    renderFiscalBenefit(machine, benefit) {
        const isAdmin = Auth.isAdministration();
        const operations = [
            ['fatture', 'Fatture'],
            ['documenti_trasporto', 'Documenti di trasporto'],
            ['ordini_acquisto', 'Ordini di acquisto'],
            ['contabili_pagamento', 'Contabili di pagamento'],
            ['perizia_asseverata', 'Perizia asseverata'],
            ['attestazione_contabile', 'Attestazione contabile'],
            ['comunicazione_preventiva', 'Comunicazione preventiva'],
            ['comunicazione_intermedia', 'Comunicazione intermedia'],
            ['comunicazione_consuntivo', 'Comunicazione a consuntivo'],
        ];
        const docs = benefit?.documents || [];
        const docMap = Object.fromEntries(docs.map(doc => [doc.operation, doc]));
        const maintenanceYears = benefit?.maintenance_years || [];
        let html = '<div class="detail-section">';
        html += `<div class="detail-section-title">Operazioni da completare</div>`;
        html += '<div class="documents-list">';
        operations.forEach(([value, label]) => {
            const operationDoc = docMap[value];
            html += `<div class="doc-item">`;
            html += `<div class="doc-details"><button class="btn btn-link fiscal-benefit-operation" style="padding:0;text-align:left;font-weight:700;" onclick="Dashboard.showFiscalBenefitDocuments(${machine.id}, '${value}', '${label.replace(/'/g, "\\'")}')">${label}</button></div>`;
            html += `<div class="doc-actions">`;
            if (isAdmin) {
                html += `<button class="btn btn-secondary btn-sm" onclick="Dashboard.uploadFiscalBenefitDocument(${machine.id}, '${value}')">Carica</button>`;
            }
            html += `</div></div>`;
        });
        html += '</div>';

        if (maintenanceYears.length) {
            html += `<div class="detail-section" style="margin-top:1rem;">
                <div class="detail-section-title">Documenti mantenimento per anno</div>
                <div class="documents-list">`;
            maintenanceYears.forEach(yearItem => {
                const yearDocs = yearItem.documents || [];
                html += `<div class="doc-item" style="flex-direction:column;align-items:flex-start;gap:0.35rem;padding:0.8rem 0.9rem;border:1px solid var(--border-color);border-radius:10px;background:rgba(59,130,246,0.04);">
                    <div class="doc-name" style="font-weight:700;">Anno ${yearItem.anno}</div>`;
                if (yearDocs.length) {
                    yearDocs.forEach(doc => {
                        html += `<a href="${doc.file}" target="_blank" style="display:inline-flex;align-items:center;gap:0.35rem;color:var(--color-primary);font-weight:600;">📄 Comunicazione periodica</a>`;
                    });
                } else {
                    html += `<div class="doc-meta">Nessun documento caricato.</div>`;
                }
                html += `</div>`;
            });
            html += '</div></div>';
        }

        if (isAdmin) {
            html += `<div class="form-actions" style="margin-top:1rem;">
                <button class="btn btn-primary" onclick="Dashboard.showMaintenanceForm(${machine.id})">Mantenimento</button>
                <button class="btn btn-secondary" onclick="Dashboard.closeBenefitFiscal(${machine.id})">Chiusura beneficio</button>
            </div>`;
        }
        html += '</div>';
        return html;
    },

    async showMaintenanceForm(machineId) {
        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');
        title.textContent = 'Mantenimento beneficio fiscale';
        body.innerHTML = `
            <form class="modal-form" id="maintenance-form">
                <input type="hidden" name="machine_id" value="${machineId}">
                <div class="form-group">
                    <label>Anno</label>
                    <input type="number" name="anno" required>
                </div>
                <div class="form-group">
                    <label>Documenti comunicazione periodica</label>
                    <input type="file" name="files" multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="Dashboard.closeFormModal()">Annulla</button>
                    <button type="submit" class="btn btn-primary">Salva</button>
                </div>
            </form>
        `;
        modal.style.display = 'flex';

        document.getElementById('maintenance-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            try {
                await API.createFiscalBenefitMaintenance(machineId, formData);
                Components.toast('Mantenimento salvato.', 'success');
                this.closeFormModal();
                this.showFiscalBenefit(machineId);
            } catch (err) {
                Components.toast(err.message, 'error');
            }
        });
    },

    async showFiscalBenefitDocuments(machineId, operation, label) {
        const modal = document.getElementById('machine-modal');
        const body = document.getElementById('modal-body');
        const title = document.getElementById('modal-title');
        title.textContent = `${label} - Documenti`;
        body.innerHTML = '<div class="loading-placeholder">Caricamento documenti...</div>';
        modal.style.display = 'flex';

        try {
            const benefit = await API.getFiscalBenefit(machineId);
            const machine = await API.getMachine(machineId);
            const techDocsMap = {
                'documenti_trasporto': 'BOLLA_TRASPORTO',
                'ordini_acquisto': 'ORDINE_MACCHINA'
            };
            const mappedType = techDocsMap[operation];
            const techDocs = mappedType ? (machine.documents || []).filter(d => d.tipo_documento === mappedType) : [];
            const docs = (benefit?.documents || []).filter(doc => doc.operation === operation);
            
            let html = '<div class="detail-section">';
            html += `<div class="detail-section-title">${label}</div>`;
            html += '<div class="documents-list">';
            if (!docs.length && !techDocs.length) {
                html += '<div class="empty-state"><p>Nessun documento caricato per questa fase.</p></div>';
            } else {
                docs.forEach(doc => {
                    const filename = doc.file ? doc.file.split('/').pop() : 'Documento';
                    html += `<div class="doc-item">
                        <div class="doc-details">
                            <div class="doc-name">${filename}</div>
                            <div class="doc-meta">${Components.formatDate(doc.uploaded_at)}</div>
                        </div>
                        <div class="doc-actions">
                            <a href="${doc.file}" target="_blank" class="btn-icon" title="Scarica">⬇</a>
                            <button class="btn-icon" title="Elimina" onclick="Dashboard.deleteFiscalBenefitDocument(${machineId}, ${doc.id}, '${operation}')">🗑</button>
                        </div>
                    </div>`;
                });
                techDocs.forEach(doc => {
                    const filename = doc.file ? doc.file.split('/').pop() : 'Documento';
                    html += `<div class="doc-item" style="background: rgba(16,185,129,0.05); border-left: 3px solid #10b981;">
                        <div class="doc-details">
                            <div class="doc-name">${filename} <span class="status-badge" style="background:#10b981;color:white;font-size:0.65rem;margin-left:0.5rem;padding:0.15rem 0.4rem;">Tech</span></div>
                            <div class="doc-meta">Caricato da Ufficio Tecnico • ${Components.formatDate(doc.uploaded_at)}</div>
                        </div>
                        <div class="doc-actions">
                            <a href="${doc.file}" target="_blank" class="btn-icon" title="Scarica">⬇</a>
                        </div>
                    </div>`;
                });
            }
            html += '</div></div>';
            body.innerHTML = html;
        } catch (err) {
            body.innerHTML = `<div class="empty-state"><p>Errore: ${err.message}</p></div>`;
        }
    },

    async uploadFiscalBenefitDocument(machineId, operation) {
        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');
        title.textContent = 'Carica documento beneficio fiscale';
        body.innerHTML = `
            <form class="modal-form" id="fiscal-doc-form">
                <input type="hidden" name="machine_id" value="${machineId}">
                <input type="hidden" name="operation" value="${operation}">
                <div class="form-group">
                    <label>Documenti</label>
                    <input type="file" name="files" multiple required accept=".pdf,.doc,.docx,.jpg,.jpeg,.png">
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="Dashboard.closeFormModal()">Annulla</button>
                    <button type="submit" class="btn btn-primary">Carica</button>
                </div>
            </form>
        `;
        modal.style.display = 'flex';

        document.getElementById('fiscal-doc-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            try {
                await API.uploadFiscalBenefitDocument(machineId, formData);
                Components.toast('Documento caricato.', 'success');
                this.closeFormModal();
                this.showFiscalBenefit(machineId);
            } catch (err) {
                Components.toast(err.message, 'error');
            }
        });
    },

    async deleteFiscalBenefitDocument(machineId, docId, operation) {
        const confirmed = window.confirm('Eliminare questo documento del beneficio fiscale?');
        if (!confirmed) return;

        try {
            await API.deleteFiscalBenefitDocument(machineId, docId);
            Components.toast('Documento eliminato.', 'success');
            this.showFiscalBenefitDocuments(machineId, operation, operation.replace(/_/g, ' '));
        } catch (err) {
            Components.toast(err.message, 'error');
        }
    },

    async closeBenefitFiscal(machineId) {
        try {
            await API.closeFiscalBenefit(machineId);
            Components.toast('Beneficio chiuso.', 'success');
            this.showFiscalBenefit(machineId);
        } catch (err) {
            Components.toast(err.message, 'error');
        }
    },

    showUploadForm(machineId, type, checklistItemId = null, requiredDocumentTypes = '') {
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
        const documentTypes = Array.isArray(requiredDocumentTypes)
            ? requiredDocumentTypes
            : requiredDocumentTypes ? requiredDocumentTypes.split(',') : [];
        body.innerHTML = Components.renderUploadForm(machineId, type, checklistItemId, documentTypes);
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

    async deleteDocument(machineId, docId, type) {
        const confirmed = window.confirm('Eliminare questo documento?');
        if (!confirmed) return;

        try {
            if (type === 'admin') {
                await API.deleteAdminDocument(machineId, docId);
            } else {
                await API.deleteDocument(machineId, docId);
            }
            Components.toast('Documento eliminato.', 'success');
            this.showMachineDetail(machineId);
        } catch (err) {
            Components.toast(err.message, 'error');
        }
    },

    closeFormModal() {
        document.getElementById('form-modal').style.display = 'none';
    },

    async showInterconnessioneForm(machineId) {
        const modal = document.getElementById('form-modal');
        const body = document.getElementById('form-modal-body');
        const title = document.getElementById('form-modal-title');
        title.textContent = 'Gestione Interconnessione';
        body.innerHTML = '<div class="loading-placeholder">Caricamento...</div>';
        modal.style.display = 'flex';

        try {
            const data = await API.getInterconnessione(machineId);
            const prevista = data.interconnessione_prevista;
            const dataPrevista = data.data_interconnessione_prevista || '';

            body.innerHTML = `
                <form class="modal-form" id="interconnessione-form">
                    <input type="hidden" name="machine_id" value="${machineId}">
                    <div class="form-group">
                        <label>L'interconnessione è prevista per questo macchinario?</label>
                        <div class="machine-type-options">
                            <label class="machine-type-option">
                                <input type="radio" name="interconnessione_prevista" value="true" ${prevista === true ? 'checked' : ''} required>
                                <span><strong>Sì</strong><small>L'interconnessione è prevista</small></span>
                            </label>
                            <label class="machine-type-option">
                                <input type="radio" name="interconnessione_prevista" value="false" ${prevista === false ? 'checked' : ''} required>
                                <span><strong>No</strong><small>L'interconnessione non è prevista</small></span>
                            </label>
                        </div>
                    </div>
                    <div class="form-group" id="data-interconnessione-group" ${prevista !== true ? 'style="display:none;"' : ''}>
                        <label>Data prevista per l'interconnessione *</label>
                        <input type="date" name="data_interconnessione_prevista" value="${dataPrevista}">
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="Dashboard.closeFormModal()">Annulla</button>
                        <button type="submit" class="btn btn-primary">Salva</button>
                    </div>
                </form>
            `;

            // Toggle data field visibility
            const radios = document.querySelectorAll('input[name="interconnessione_prevista"]');
            const dataGroup = document.getElementById('data-interconnessione-group');
            radios.forEach(radio => {
                radio.addEventListener('change', () => {
                    const isPrevista = document.querySelector('input[name="interconnessione_prevista"]:checked')?.value === 'true';
                    dataGroup.style.display = isPrevista ? '' : 'none';
                    const dateInput = dataGroup.querySelector('input[type="date"]');
                    if (!isPrevista) dateInput.value = '';
                });
            });

            document.getElementById('interconnessione-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const isPrevista = formData.get('interconnessione_prevista') === 'true';
                const payload = {
                    interconnessione_prevista: isPrevista,
                };
                if (isPrevista) {
                    const dataPrev = formData.get('data_interconnessione_prevista');
                    if (!dataPrev) {
                        Components.toast('Inserisci la data prevista per l\'interconnessione.', 'error');
                        return;
                    }
                    payload.data_interconnessione_prevista = dataPrev;
                }

                try {
                    await API.updateInterconnessione(machineId, payload);
                    Components.toast('Interconnessione aggiornata con successo!', 'success');
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
};
