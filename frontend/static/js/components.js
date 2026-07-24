// Questo file contiene i componenti UI riutilizzabili per la dashboard.

/**
 * components.js — Componenti UI riutilizzabili
 */

const Components = {

    // === BADGE DI STATO ===
    statusBadge(stato) {
        const labels = {
            'in_costruzione': 'In costruzione',
            'attiva': 'Attiva',
            'ferma': 'Ferma',
            'in_manutenzione': 'In Manutenzione',
            'dismessa': 'Dismessa',
        };
        const label = labels[stato] || stato;
        return `<span class="status-badge status-badge--${stato}"><span class="dot"></span>${label}</span>`;
    },

    // === NOTIFICHE TOAST ===
    toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const icons = {
            success: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#EF4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            info: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        };

        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.innerHTML = `${icons[type] || icons.info}<span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('removing');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    // === FORMATTA NUMERO ===
    formatNumber(num) {
        if (num === null || num === undefined) return '—';
        return new Intl.NumberFormat('it-IT').format(num);
    },

    // === FORMATTA DATA ===
    formatDate(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleDateString('it-IT', {
            day: '2-digit', month: '2-digit', year: 'numeric'
        });
    },

    formatDateTime(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleDateString('it-IT', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
    },

    formatTime(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        return d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    },

    // === RENDER MODALE DETTAGLIO MACCHINARIO ===
    renderMachineDetail(machine) {
        let tabs = ['Generale'];
        let tabContents = [];

        // Scheda: Generale (sempre visibile)
        tabs.push('');
        let generalHtml = `
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">CDL</span>
                    <span class="detail-value">${machine.cdl || '-'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">CC</span>
                    <span class="detail-value">${machine.cc || '-'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Stato</span>
                    <span class="detail-value">${machine.stato === 'in_costruzione'
                        ? `<button class="status-button" onclick="Dashboard.showChecklist(${machine.id})">${this.statusBadge(machine.stato)}</button>`
                        : this.statusBadge(machine.stato)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Tipo macchina</span>
                    <span class="detail-value">${machine.tipo_macchina === 'ACQUISTO_DIRETTO'
                        ? 'Macchina ad acquisto diretto' : 'Macchina complessa'}</span>
                </div>
                ${machine.tipo_macchina === 'ACQUISTO_DIRETTO' ? `
                    <div class="detail-item">
                        <span class="detail-label">Commessa</span>
                        <span class="detail-value">${machine.commessa || '—'}</span>
                    </div>
                ` : `
                    <div class="detail-item">
                        <span class="detail-label">Commessa macchina</span>
                        <span class="detail-value">${machine.commessa_macchina || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Commessa automazione</span>
                        <span class="detail-value">${machine.commessa_automazione || '—'}</span>
                    </div>
                `}
                <div class="detail-item">
                    <span class="detail-label">Capannone</span>
                    <span class="detail-value">${machine.capannone}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Anno Avviamento</span>
                    <span class="detail-value">${machine.anno_avviamento || '—'}</span>
                </div>
            </div>
        `;

        // Sezione log di stato (per IT)
        if (Auth.hasAnyPermission('MachineStatusLog')) {
            const ls = machine.latest_status;
            generalHtml += `
                <div class="detail-section" style="margin-top:1.25rem;">
                    <div class="detail-section-title">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                        Stato Live (PLC)
                    </div>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <span class="detail-label">Pezzi Buoni</span>
                            <span class="detail-value pezzi" style="color:var(--color-active);font-size:1.2rem;font-weight:700;">${ls ? this.formatNumber(ls.pezzi_buoni) : '—'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Fermi Macchina</span>
                            <span class="detail-value" style="color:var(--color-stopped);font-size:1.2rem;font-weight:700;">${ls ? this.formatNumber(ls.fermi_macchina) : '—'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Orario Ultimo Fermo</span>
                            <span class="detail-value">${ls && ls.orario_fermo ? this.formatDateTime(ls.orario_fermo) : '—'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Motivo Fermo</span>
                            <span class="detail-value">${ls && ls.motivo_fermo ? ls.motivo_fermo : '—'}</span>
                        </div>
                    </div>
                </div>
            `;
        }

        // Costruisce l'array delle schede
        let tabsHtml = ['Generale'];
        let contentsHtml = [generalHtml];

        // Scheda: Dati IT (visibile all'ufficio IT)
        if (Auth.hasAnyPermission('MachineITData')) {
            tabsHtml.push('Dati IT');
            const itd = machine.it_data || {};
            contentsHtml.push(`
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Tipo Accentratore</span>
                        <span class="detail-value">${itd.tipo_accentratore || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Indirizzo IP</span>
                        <span class="detail-value" style="font-family:monospace;">${itd.indirizzo_ip || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Note IT</span>
                        <span class="detail-value">${itd.note_it || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Ultimo aggiornamento</span>
                        <span class="detail-value">${itd.updated_by_name ? itd.updated_by_name + ' - ' : ''}${this.formatDateTime(itd.updated_at)}</span>
                    </div>
                </div>
            `);
        }

        // Scheda: Dati tecnici (visibile all'ufficio tecnico)
        if (Auth.hasAnyPermission('MachineTechData')) {
            tabsHtml.push('Dati Tecnici');
            const td = machine.tech_data || {};
            contentsHtml.push(`
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">Marca</span>
                        <span class="detail-value">${td.marca || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Modello</span>
                        <span class="detail-value">${td.modello || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Anno Costruzione</span>
                        <span class="detail-value">${td.anno_costruzione || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Descrizione Tecnica</span>
                        <span class="detail-value">${td.descrizione_tecnica || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Note Tecniche</span>
                        <span class="detail-value">${td.note_tecniche || '—'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Ultimo aggiornamento</span>
                        <span class="detail-value">${td.updated_by_name ? td.updated_by_name + ' - ' : ''}${this.formatDateTime(td.updated_at)}</span>
                    </div>
                </div>
            `);
        }

        // Scheda: Documenti tecnici
        if (Auth.canViewDocumentType('tech')) {
            tabsHtml.push('Documenti Tecnici');
            const docs = machine.documents || [];
            let docsHtml = '<div class="documents-list">';
            if (docs.length === 0) {
                docsHtml += '<div class="empty-state"><p>Nessun documento tecnico caricato.</p></div>';
            } else {
                docs.forEach(doc => {
                    docsHtml += `
                        <div class="doc-item">
                            <div class="doc-info">
                                <div class="doc-icon">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><polyline points="14 2 14 8 20 8"/></svg>
                                </div>
                                <div class="doc-details">
                                    <div class="doc-name">${doc.tipo_documento_display}</div>
                                    <div class="doc-meta">${doc.nome_file} • ${doc.uploaded_by_name || ''} • ${this.formatDate(doc.uploaded_at)}</div>
                                </div>
                            </div>
                            <div class="doc-actions">
                                <a href="${doc.file}" target="_blank" class="btn-icon" title="Scarica">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                                </a>
                            </div>
                        </div>
                    `;
                });
            }

            // Area di caricamento (solo per il reparto tecnico)
            if (Auth.canUploadDocumentType('tech')) {
                docsHtml += `
                    <div class="upload-area" onclick="Dashboard.showUploadForm(${machine.id}, 'tech')">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        <p>Clicca per caricare un documento</p>
                        <span>PDF, DOC, XLS, IMG — Max 10MB</span>
                    </div>
                `;
            }

            docsHtml += '</div>';
            contentsHtml.push(docsHtml);
        }

        // Scheda: Documenti amministrativi
        if (Auth.canViewDocumentType('admin')) {
            tabsHtml.push('Documenti Amministrazione');
            const adocs = machine.admin_documents || [];
            let adocsHtml = '<div class="documents-list">';
            if (adocs.length === 0) {
                adocsHtml += '<div class="empty-state"><p>Nessun documento amministrativo caricato.</p></div>';
            } else {
                adocs.forEach(doc => {
                    adocsHtml += `
                        <div class="doc-item">
                            <div class="doc-info">
                                <div class="doc-icon" style="background:rgba(16,185,129,0.12);color:#10B981;">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><polyline points="14 2 14 8 20 8"/></svg>
                                </div>
                                <div class="doc-details">
                                    <div class="doc-name">${doc.tipo_documento_display} — N. ${doc.numero_documento}</div>
                                    <div class="doc-meta">
                                        ${doc.fornitore ? doc.fornitore + ' • ' : ''}
                                        ${doc.importo ? '€ ' + parseFloat(doc.importo).toLocaleString('it-IT', {minimumFractionDigits: 2}) + ' • ' : ''}
                                        ${this.formatDate(doc.data_documento)}
                                    </div>
                                </div>
                            </div>
                            <div class="doc-actions">
                                ${doc.file ? `<a href="${doc.file}" target="_blank" class="btn-icon" title="Scarica"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></a>` : ''}
                            </div>
                        </div>
                    `;
                });
            }

            // Area di caricamento (solo per l'amministrazione)
            if (Auth.canUploadDocumentType('admin')) {
                adocsHtml += `
                    <div class="upload-area" onclick="Dashboard.showUploadForm(${machine.id}, 'admin')">
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        <p>Clicca per caricare un documento amministrativo</p>
                        <span>Fatture, Bolle, Ordini, Pagamenti</span>
                    </div>
                `;
            }

            adocsHtml += '</div>';
            contentsHtml.push(adocsHtml);
        }

        // Costruisce l'HTML finale
        let html = '<div class="tabs">';
        tabsHtml.forEach((tab, i) => {
            html += `<button class="tab-btn ${i === 0 ? 'active' : ''}" data-tab="${i}">${tab}</button>`;
        });
        html += '</div>';

        contentsHtml.forEach((content, i) => {
            html += `<div class="tab-content ${i === 0 ? 'active' : ''}" data-tab-content="${i}">${content}</div>`;
        });

        // Pulsante di modifica
        let canEditAnything = Auth.canWrite('Machine', 'cdl') ||
                              Auth.canWrite('Machine', 'cc') ||
                              Auth.canWrite('Machine', 'capannone') ||
                              Auth.canWrite('Machine', 'anno_avviamento') ||
                              Auth.canWrite('MachineITData', 'tipo_accentratore') ||
                              Auth.canWrite('MachineITData', 'indirizzo_ip') ||
                              Auth.canWrite('MachineTechData', 'marca');

        if (canEditAnything) {
            html += `
                <div class="form-actions" style="margin-top:1rem;">
                    <button class="btn btn-primary" onclick="Dashboard.showEditForm(${machine.id})">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>
                        Modifica Dati
                    </button>
                </div>
            `;
        }

        if (Auth.isTechnicalOffice() || Auth.getUser()?.is_superuser) {
            html += `
                <div class="form-actions machine-delete-actions" style="margin-top:0.5rem;">
                    <button class="btn btn-danger" onclick="Dashboard.deleteMachine(${machine.id})">
                        Elimina Macchinario
                    </button>
                </div>
            `;
        }

        return html;
    },

    // === RENDER FORM DI MODIFICA ===
    renderEditForm(machine) {
        const canWriteField = (model, field) => Auth.canWrite(model, field);
        const fieldClass = (model, field) => canWriteField(model, field) ? '' : 'field-readonly';

        let html = '<form class="modal-form" id="edit-machine-form">';
        html += `<input type="hidden" name="machine_id" value="${machine.id}">`;

        // Campi base del macchinario
        html += '<div class="detail-section-title">Dati Base Macchinario</div>';
        html += '<div class="form-row">';
        html += `
            <div class="form-group ${fieldClass('Machine', 'cdl')}">
                <label>CDL</label>
                <input type="text" name="cdl" value="${machine.cdl || ''}" ${!canWriteField('Machine', 'cdl') ? 'readonly' : ''}>
            </div>
            <div class="form-group ${fieldClass('Machine', 'cc')}">
                <label>CC</label>
                <input type="text" name="cc" value="${machine.cc || ''}" ${!canWriteField('Machine', 'cc') ? 'readonly' : ''}>
            </div>
            <div class="form-group ${fieldClass('Machine', 'capannone')}">
                <label>Capannone</label>
                <input type="text" name="capannone" value="${machine.capannone || ''}" ${!canWriteField('Machine', 'capannone') ? 'readonly' : ''}>
            </div>
        `;
        html += '</div><div class="form-row">';
        html += `
            <div class="form-group ${fieldClass('Machine', 'anno_avviamento')}">
                <label>Anno Avviamento</label>
                <input type="number" name="anno_avviamento" value="${machine.anno_avviamento || ''}" ${!canWriteField('Machine', 'anno_avviamento') ? 'readonly' : ''}>
            </div>
            <div class="form-group field-readonly">
                <label>Stato</label>
                <input type="text" value="${machine.stato}" readonly>
            </div>
        `;
        html += '</div>';

        // Campi dati IT
        if (Auth.hasAnyPermission('MachineITData')) {
            const itd = machine.it_data || {};
            html += '<div class="detail-section-title" style="margin-top:1.25rem;">Dati IT</div>';
            html += '<div class="form-row">';
            html += `
                <div class="form-group ${fieldClass('MachineITData', 'tipo_accentratore')}">
                    <label>Tipo Accentratore</label>
                    <select name="tipo_accentratore" ${!canWriteField('MachineITData', 'tipo_accentratore') ? 'disabled' : ''}>
                        <option value="">—</option>
                        <option value="IOX" ${itd.tipo_accentratore === 'IOX' ? 'selected' : ''}>IOX</option>
                        <option value="RIO" ${itd.tipo_accentratore === 'RIO' ? 'selected' : ''}>RIO</option>
                        <option value="PLC" ${itd.tipo_accentratore === 'PLC' ? 'selected' : ''}>PLC</option>
                    </select>
                </div>
                <div class="form-group ${fieldClass('MachineITData', 'indirizzo_ip')}">
                    <label>Indirizzo IP</label>
                    <input type="text" name="indirizzo_ip" value="${itd.indirizzo_ip || ''}" placeholder="192.168.1.x" ${!canWriteField('MachineITData', 'indirizzo_ip') ? 'readonly' : ''}>
                </div>
            `;
            html += '</div>';
            html += `
                <div class="form-group ${fieldClass('MachineITData', 'note_it')}">
                    <label>Note IT</label>
                    <textarea name="note_it" rows="2" ${!canWriteField('MachineITData', 'note_it') ? 'readonly' : ''}>${itd.note_it || ''}</textarea>
                </div>
            `;
        }

        // Campi dati tecnici
        if (Auth.hasAnyPermission('MachineTechData')) {
            const td = machine.tech_data || {};
            html += '<div class="detail-section-title" style="margin-top:1.25rem;">Dati Tecnici</div>';
            html += '<div class="form-row">';
            html += `
                <div class="form-group ${fieldClass('MachineTechData', 'marca')}">
                    <label>Marca</label>
                    <input type="text" name="marca" value="${td.marca || ''}" ${!canWriteField('MachineTechData', 'marca') ? 'readonly' : ''}>
                </div>
                <div class="form-group ${fieldClass('MachineTechData', 'modello')}">
                    <label>Modello</label>
                    <input type="text" name="modello" value="${td.modello || ''}" ${!canWriteField('MachineTechData', 'modello') ? 'readonly' : ''}>
                </div>
            `;
            html += '</div><div class="form-row">';
            html += `
                <div class="form-group ${fieldClass('MachineTechData', 'anno_costruzione')}">
                    <label>Anno Costruzione</label>
                    <input type="number" name="anno_costruzione" value="${td.anno_costruzione || ''}" ${!canWriteField('MachineTechData', 'anno_costruzione') ? 'readonly' : ''}>
                </div>
                <div class="form-group ${fieldClass('MachineTechData', 'descrizione_tecnica')}">
                    <label>Descrizione Tecnica</label>
                    <input type="text" name="descrizione_tecnica" value="${td.descrizione_tecnica || ''}" ${!canWriteField('MachineTechData', 'descrizione_tecnica') ? 'readonly' : ''}>
                </div>
            `;
            html += '</div>';
            html += `
                <div class="form-group ${fieldClass('MachineTechData', 'note_tecniche')}">
                    <label>Note Tecniche</label>
                    <textarea name="note_tecniche" rows="2" ${!canWriteField('MachineTechData', 'note_tecniche') ? 'readonly' : ''}>${td.note_tecniche || ''}</textarea>
                </div>
            `;
        }

        html += `
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="Dashboard.closeFormModal()">Annulla</button>
                <button type="submit" class="btn btn-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                    Salva Modifiche
                </button>
            </div>
        `;
        html += '</form>';

        return html;
    },

    // === RENDER FORM DI CREAZIONE ===
    renderCreateForm(locations = []) {
        let html = '<form class="modal-form" id="create-machine-form">';

        html += '<div class="form-row">';
        html += `
           <div class="form-group">
                <label>CDL *</label>
                <input type="text" name="cdl" required placeholder="Es. CDL-01">
            </div>
            <div class="form-group">
                <label>CC *</label>
                <input type="text" name="cc" required placeholder="Es. CC-100">
            </div>
            <div class="form-group">
                <label>Capannone *</label>
                <select name="capannone" required>
                    <option value="">Seleziona una località...</option>
                    ${locations.map(location => `<option value="${location}">${location}</option>`).join('')}
                </select>
            </div>
        `;
        html += '</div><div class="form-row">';
        html += `
            <div class="form-group">
                <label>Anno Avviamento</label>
                <input type="number" name="anno_avviamento" placeholder="Es. 2023">
            </div>
            <div class="form-group">
                <label>Tipo macchina *</label>
                <div class="machine-type-options">
                    <label class="machine-type-option">
                        <input type="radio" name="tipo_macchina" value="COMPLESSA" required>
                        <span><strong>Macchina complessa</strong><small>Costruzione e assemblaggio interno</small></span>
                    </label>
                    <label class="machine-type-option">
                        <input type="radio" name="tipo_macchina" value="ACQUISTO_DIRETTO" required>
                        <span><strong>Macchina ad acquisto diretto</strong><small>Macchina acquistata e posizionata</small></span>
                    </label>
                </div>
            </div>
        `;
        html += '</div>';

        html += `
            <div class="machine-order-fields" id="machine-order-fields">
                <div class="form-group machine-order-field" data-machine-type="ACQUISTO_DIRETTO" hidden>
                    <label>Commessa *</label>
                    <input type="text" name="commessa" placeholder="Inserisci la commessa">
                </div>
                <div class="form-row" data-machine-type="COMPLESSA" hidden>
                    <div class="form-group machine-order-field">
                        <label>Commessa macchina *</label>
                        <input type="text" name="commessa_macchina" placeholder="Inserisci la commessa macchina">
                    </div>
                    <div class="form-group machine-order-field">
                        <label>Commessa automazione *</label>
                        <input type="text" name="commessa_automazione" placeholder="Inserisci la commessa automazione">
                    </div>
                </div>
            </div>
        `;

        html += `
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="Dashboard.closeFormModal()">Annulla</button>
                <button type="submit" class="btn btn-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Crea Macchinario
                </button>
            </div>
        `;
        html += '</form>';

        return html;
    },

    // === RENDER FORM DI CARICAMENTO ===
    renderUploadForm(machineId, type, checklistItemId = null, requiredDocumentTypes = []) {
        const isAdmin = type === 'admin';
        if (!Auth.canUploadDocumentType(type)) {
            return `<div class="empty-state"><p>Non hai i permessi per caricare questo tipo di documento.</p></div>`;
        }

        let html = `<form class="modal-form" id="upload-doc-form" enctype="multipart/form-data">`;
        html += `<input type="hidden" name="machine_id" value="${machineId}">`;
        html += `<input type="hidden" name="doc_type" value="${type}">`;
        if (checklistItemId) {
            html += `<input type="hidden" name="checklist_item_id" value="${checklistItemId}">`;
        }

        html += `
            <div class="form-group">
                <label>Tipo Documento *</label>
                <select name="tipo_documento" required>
                    <option value="">Seleziona...</option>
        `;

        if (isAdmin) {
            html += `
                <option value="FATTURA">Fattura</option>
                <option value="BOLLA_TRASPORTO">Bolla di Trasporto</option>
                <option value="ORDINE_ACQUISTO">Ordine di Acquisto</option>
                <option value="COPIA_PAGAMENTO">Copia Pagamento</option>
                <option value="PERIZIA_CONSULENTE">Perizia consulente</option>
                <option value="ALTRO_ADMIN">Altro</option>
            `;
        } else {
            const technicalDocumentOptions = [
                ['BOLLA_TRASPORTO', 'Documento di Trasporto'],
                ['USO_MANUTENZIONE', 'Manuale Uso e Manutenzione'],
                ['CERTIFICAZIONE_CE', 'Certificazione CE'],
                ['SCHEDA_VDR', 'Scheda VDR'],
                ['VERBALE_COLLAUDO', 'Verbale di Collaudo'],
                ['ALTRO', 'Altro'],
            ].filter(([value]) => !requiredDocumentTypes.length || requiredDocumentTypes.includes(value));
            html += `
                ${technicalDocumentOptions.map(([value, label]) => `<option value="${value}">${label}</option>`).join('')}
            `;
        }

        html += '</select></div>';

        if (isAdmin) {
            html += '<div class="form-row">';
            html += `
                <div class="form-group">
                    <label>Numero Documento *</label>
                    <input type="text" name="numero_documento" required placeholder="Es. FT-2024/001">
                </div>
                <div class="form-group">
                    <label>Data Documento *</label>
                    <input type="date" name="data_documento" required>
                </div>
            `;
            html += '</div><div class="form-row">';
            html += `
                <div class="form-group">
                    <label>Importo €</label>
                    <input type="number" name="importo" step="0.01" placeholder="0.00">
                </div>
                <div class="form-group">
                    <label>Fornitore</label>
                    <input type="text" name="fornitore" placeholder="Nome fornitore">
                </div>
            `;
            html += '</div>';
            html += `
                <div class="form-group">
                    <label>Descrizione</label>
                    <textarea name="descrizione" rows="2" placeholder="Note aggiuntive..."></textarea>
                </div>
            `;
        }

        html += `
            <div class="form-group">
                <label>File${isAdmin ? '' : ' *'}</label>
                <input type="file" name="file" ${isAdmin ? '' : 'required'} accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png">
            </div>
        `;

        html += `
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="Dashboard.closeFormModal()">Annulla</button>
                <button type="submit" class="btn btn-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    Carica Documento
                </button>
            </div>
        `;
        html += '</form>';

        return html;
    },

    renderChecklist(machine, items) {
        const officeLabels = { TECH: 'Ufficio Tecnico', IT: 'Ufficio IT' };
        let html = `<div class="checklist-header">
            <span>${machine.tipo_macchina === 'ACQUISTO_DIRETTO'
                ? 'Macchina ad acquisto diretto' : 'Macchina complessa'}</span>
            <span>${items.filter(item => item.completata).length}/${items.length} completate</span>
        </div>`;

        ['TECH', 'IT'].forEach(office => {
            const officeItems = items.filter(item => item.ufficio === office);
            if (!officeItems.length) return;
            html += `<div class="checklist-section"><h3>${officeLabels[office]}</h3>`;
            officeItems.forEach(item => {
                const canEdit = Auth.getUserOfficeCode() === office &&
                    !(office === 'TECH' && item.solo_visualizzazione_tech) ||
                    Auth.getUser()?.is_superuser;
                const docs = item.documents || [];
                const requiredDocs = item.document_types || [];
                const missingDocs = requiredDocs.filter(type =>
                    !docs.some(doc => doc.tipo_documento === type)
                );
                html += `<div class="checklist-item ${item.completata ? 'is-complete' : ''}">
                    <label>
                        <input type="checkbox" ${item.completata ? 'checked' : ''}
                            ${canEdit && (!missingDocs.length || item.completata) ? '' : 'disabled'}
                            ${missingDocs.length ? 'title="Carica prima i documenti richiesti"' : ''}
                            onchange="Dashboard.toggleChecklistItem(${machine.id}, ${item.id}, this.checked)">
                        <span>${item.descrizione}</span>
                    </label>
                    ${requiredDocs.length ? `<div class="checklist-documents">
                        <span class="document-required-label">Richiesti: ${item.document_requirements.map(requirement => requirement.label).join(', ')}</span>
                        ${missingDocs.length
                            ? `<span class="document-warning">Mancante</span>`
                            : `<span class="document-ready">Completo</span>`}
                        ${docs.map(doc => `<a href="${doc.file}" target="_blank">${doc.tipo_documento_display}</a>`).join('')}
                        ${Auth.canUploadDocumentType('tech') ? `<button class="btn btn-secondary btn-sm" onclick="Dashboard.showUploadForm(${machine.id}, 'tech', ${item.id}, '${requiredDocs.join(',')}')">Carica</button>` : ''}
                    </div>` : ''}
                </div>`;
            });
            html += '</div>';
        });

        return html;
    },
};
