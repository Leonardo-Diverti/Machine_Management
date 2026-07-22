// Questo file gestisce la logica della dashboard e delle interazioni utente.
const Dashboard = {
    pollingInterval: null,
    currentPage: 'dashboard',

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
        if (user) {
            const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username;
            document.getElementById('user-name').textContent = fullName;
            document.getElementById('user-avatar').textContent =
                (user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username[0].toUpperCase();
        }
        if (office) {
            document.getElementById('user-office').textContent = office.name;
            document.getElementById('office-badge-text').textContent = office.name;
            if (office.color) {
                document.getElementById('office-dot').style.background = office.color;
            }
        }
        const toolbarActions = document.getElementById('toolbar-actions');
        if (Auth.isTechnicalOffice() || (user && user.is_superuser)) {
            toolbarActions.innerHTML = `
                <button class="btn btn-primary btn-sm" onclick="Dashboard.showCreateForm()">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Nuovo Macchinario
                </button>
            `;
        } else {
            toolbarActions.innerHTML = '';
        }
    },

    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(item.dataset.page);
            });
        });
        document.querySelectorAll('.card-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.navigateTo(link.dataset.page);
            });
        });
    },

    navigateTo(page) {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const activeNav = document.querySelector(`[data-page="${page}"]`);
        if (activeNav) activeNav.classList.add('active');

        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const activePage = document.getElementById(`page-${page}`);
        if (activePage) activePage.classList.add('active');

        const titles = { 'dashboard': 'Dashboard', 'machines': 'Macchinari', 'live': 'Stato Live' };
        document.getElementById('page-title').textContent = titles[page] || page;
        this.currentPage = page;

        if (page === 'machines') this.loadMachinesTable();
        if (page === 'live') this.loadLiveStatus();

        document.getElementById('sidebar').classList.remove('open');
        const overlay = document.querySelector('.sidebar-overlay');
        if (overlay) overlay.classList.remove('active');
    },

    setupEventListeners() {
        let searchTimeout;
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => this.loadMachinesTable(), 300);
            });
        }
        const filterStato = document.getElementById('filter-stato');
        if (filterStato) filterStato.addEventListener('change', () => this.loadMachinesTable());
        
        const filterCapannone = document.getElementById('filter-capannone');
        if (filterCapannone) filterCapannone.addEventListener('change', () => this.loadMachinesTable());

        document.getElementById('modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('form-modal-close').addEventListener('click', () => this.closeFormModal());

        document.getElementById('machine-modal').addEventListener('click', (e) => {
            if (e.target.id === 'machine-modal') this.closeModal();
        });
        document.getElementById('form-modal').addEventListener('click', (e) => {
            if (e.target.id === 'form-modal') this.closeFormModal();
        });

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

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
                this.closeFormModal();
            }
        });
    },

    async loadDashboard() {
        try {
            const stats = await API.getMachineStats();
            this.animateNumber('stat-total', stats.totale);
            this.animateNumber('stat-active', stats.attive);
            this.animateNumber('stat-stopped', stats.ferme);
            this.animateNumber('stat-maintenance', stats.in_manutenzione);

            const machinesData = await API.getMachines({ page_size: 5 });
            const machines = machinesData.results || machinesData;
            this.renderRecentMachines(machines);

            const liveData = await API.getLiveStatus();
            this.renderLivePreview(liveData);
        } catch (err) {
            Components.toast('Errore nel caricamento della dashboard', 'error');
        }
    },

    async loadMachinesTable() {
        const tbody = document.getElementById('machines-tbody');
        tbody.innerHTML = '<tr><td colspan="8" class="loading-placeholder">Caricamento macchinari...</td></tr>';
        try {
            const search = document.getElementById('search-input').value;
            const stato = document.getElementById('filter-stato').value;
            const capannone = document.getElementById('filter-capannone').value;

            const params = {};
            if (search) params.search = search;
            if (stato) params.stato = stato;
            if (capannone) params.capannone = capannone;

            const data = await API.getMachines(params);
            const machines = data.results || data;

            if (machines.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Nessun macchinario trovato.</td></tr>';
                return;
            }

            const user = Auth.getUser();
            const officeCode = Auth.getUserOfficeCode();
            const showProduction = (user && user.is_superuser) || officeCode === 'TECH' || officeCode === 'IT';

            document.querySelectorAll('.col-production').forEach(el => {
                el.style.display = showProduction ? '' : 'none';
            });

            let html = '';
            machines.forEach(m => {
                const ls = m.latest_status;
                html += `
                    <tr onclick="Dashboard.openMachineModal(${m.id})" style="cursor:pointer;">
                        <td><strong>${m.cdl || '-'}</strong></td>
                        <td>${m.cc || '-'}</td>
                        <td>${m.capannone}</td>
                        <td>${m.anno_avviamento || '-'}</td>
                        <td>${Components.statusBadge(m.stato)}</td>
                        ${showProduction ? `
                            <td class="col-production" style="font-weight:600;color:var(--color-active);">${ls && ls.pezzi_buoni ? Components.formatNumber(ls.pezzi_buoni) : '0'}</td>
                            <td class="col-production" style="font-size:0.85rem;color:var(--text-secondary);">${ls && ls.motivo_fermo ? ls.motivo_fermo : '-'}</td>
                        ` : ''}
                        <td>
                            <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); Dashboard.openMachineModal(${m.id})">Dettagli</button>
                        </td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="8" class="empty-state" style="color:var(--color-danger);">Errore: ${err.message}</td></tr>`;
        }
    },

    async loadLiveStatus() {
        const grid = document.getElementById('live-grid');
        try {
            const data = await API.getLiveStatus();
            if (data.length === 0) {
                grid.innerHTML = '<div class="empty-state"><p>Nessun macchinario in stato live.</p></div>';
                return;
            }
            let html = '';
            data.forEach(m => {
                html += `
                    <div class="live-card" onclick="Dashboard.openMachineModal(${m.id})" style="cursor:pointer;">
                        <div class="live-card-header">
                            <span class="live-card-title">${m.cdl || '-'} (${m.cc || '-'})</span>
                            ${Components.statusBadge(m.stato)}
                        </div>
                        <div class="live-card-body">
                            <div class="live-stat">
                                <span class="label">Capannone:</span>
                                <span class="value">${m.capannone}</span>
                            </div>
                            <div class="live-stat">
                                <span class="label">Pezzi Buoni:</span>
                                <span class="value" style="color:var(--color-active);font-weight:700;">${Components.formatNumber(m.pezzi_buoni)}</span>
                            </div>
                            <div class="live-stat">
                                <span class="label">Motivo Fermo:</span>
                                <span class="value">${m.motivo_fermo || '-'}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            grid.innerHTML = html;
        } catch (err) {
            grid.innerHTML = '<div class="empty-state">Errore nel caricamento dello stato live.</div>';
        }
    },

    renderRecentMachines(machines) {
        const container = document.getElementById('recent-machines');
        if (!machines || machines.length === 0) {
            container.innerHTML = '<p class="empty-state">Nessun macchinario.</p>';
            return;
        }
        let html = '<div class="machines-mini-grid">';
        machines.forEach(m => {
            html += `
                <div class="mini-machine-item" onclick="Dashboard.openMachineModal(${m.id})" style="cursor:pointer;padding:0.75rem;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong>${m.cdl || '-'}</strong> <span style="font-size:0.85rem;color:var(--text-secondary);">(${m.capannone})</span>
                    </div>
                    <div>${Components.statusBadge(m.stato)}</div>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    },

    renderLivePreview(data) {
        const container = document.getElementById('live-preview');
        if (!data || data.length === 0) {
            container.innerHTML = '<p class="empty-state">Nessun dato live.</p>';
            return;
        }
        let html = '<div style="display:flex;flex-direction:column;gap:0.5rem;">';
        data.slice(0, 4).forEach(m => {
            html += `
                <div style="display:flex;justify-content:space-between;font-size:0.9rem;padding:0.4rem 0;border-bottom:1px solid var(--border-color);">
                    <span><strong>${m.cdl || '-'}</strong></span>
                    <span style="color:var(--color-active);font-weight:600;">${Components.formatNumber(m.pezzi_buoni)} pz</span>
                </div>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
    },

    async openMachineModal(id) {
        try {
            const machine = await API.getMachine(id);
            document.getElementById('modal-title').textContent = `Macchinario: ${machine.cdl || '-'} / ${machine.cc || '-'}`;
            document.getElementById('modal-body').innerHTML = Components.renderMachineDetail(machine);
            document.getElementById('machine-modal').style.display = 'flex';
        } catch (err) {
            Components.toast('Errore nel recupero dei dettagli', 'error');
        }
    },

    closeModal() {
        document.getElementById('machine-modal').style.display = 'none';
    },

    closeFormModal() {
        document.getElementById('form-modal').style.display = 'none';
    },

    showCreateForm() {
        document.getElementById('form-modal-title').textContent = 'Nuovo Macchinario';
        document.getElementById('form-modal-body').innerHTML = Components.renderCreateForm();
        document.getElementById('form-modal').style.display = 'flex';

        const form = document.getElementById('create-machine-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            try {
                await API.createMachine(data);
                Components.toast('Macchinario creato con successo', 'success');
                this.closeFormModal();
                this.loadMachinesTable();
            } catch (err) {
                Components.toast(err.message, 'error');
            }
        });
    },

    showEditForm(id) {
        API.getMachine(id).then(machine => {
            document.getElementById('form-modal-title').textContent = `Modifica: ${machine.cdl || '-'}`;
            document.getElementById('form-modal-body').innerHTML = Components.renderEditForm(machine);
            document.getElementById('form-modal').style.display = 'flex';

            const form = document.getElementById('edit-machine-form');
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(form);
                const data = Object.fromEntries(formData.entries());
                
                try {
                    await API.updateMachine(id, data);
                    if (Auth.hasAnyPermission('MachineITData') && (data.tipo_accentratore !== undefined || data.indirizzo_ip !== undefined || data.note_it !== undefined)) {
                        await API.updateITData(id, {
                            tipo_accentratore: data.tipo_accentratore,
                            indirizzo_ip: data.indirizzo_ip,
                            note_it: data.note_it
                        });
                    }
                    if (Auth.hasAnyPermission('MachineTechData') && (data.marca !== undefined || data.modello !== undefined)) {
                        await API.updateTechData(id, {
                            marca: data.marca,
                            modello: data.modello,
                            anno_costruzione: data.anno_costruzione,
                            descrizione_tecnica: data.descrizione_tecnica,
                            note_tecniche: data.note_tecniche
                        });
                    }
                    Components.toast('Modifiche salvate con successo', 'success');
                    this.closeFormModal();
                    this.openMachineModal(id);
                    if (this.currentPage === 'machines') this.loadMachinesTable();
                } catch (err) {
                    Components.toast(err.message, 'error');
                }
            });
        }).catch(err => {
            Components.toast('Errore nel caricamento del modulo di modifica', 'error');
        });
    },

    showUploadForm(machineId, type) {
        document.getElementById('form-modal-title').textContent = type === 'admin' ? 'Carica Documento Amministrativo' : 'Carica Documento Tecnico';
        document.getElementById('form-modal-body').innerHTML = Components.renderUploadForm(machineId, type);
        document.getElementById('form-modal').style.display = 'flex';

        const form = document.getElementById('upload-doc-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            try {
                if (type === 'admin') {
                    await API.uploadAdminDocument(machineId, formData);
                } else {
                    await API.uploadDocument(machineId, formData);
                }
                Components.toast('Documento caricato con successo', 'success');
                this.closeFormModal();
                this.openMachineModal(machineId);
            } catch (err) {
                Components.toast(err.message, 'error');
            }
        });
    },

    animateNumber(elementId, target) {
        const el = document.getElementById(elementId);
        if (!el) return;
        el.textContent = Components.formatNumber(target);
    },

    startPolling() {
        this.stopPolling();
        this.pollingInterval = setInterval(async () => {
            if (this.currentPage === 'dashboard') {
                const stats = await API.getMachineStats().catch(() => null);
                if (stats) {
                    this.animateNumber('stat-total', stats.totale);
                    this.animateNumber('stat-active', stats.attive);
                    this.animateNumber('stat-stopped', stats.ferme);
                    this.animateNumber('stat-maintenance', stats.in_manutenzione);
                }
            } else if (this.currentPage === 'machines') {
                this.loadMachinesTable();
            } else if (this.currentPage === 'live') {
                this.loadLiveStatus();
            }
        }, 10000);
    },

    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
};