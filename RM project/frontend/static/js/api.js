/**
 * api.js — Client API centralizzato
 */

const API = {
    BASE_URL: '/api',

    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const headers = options.headers || {};

        // Add auth token
        const token = Auth.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        // Don't set Content-Type for FormData (browser sets it with boundary)
        if (!(options.body instanceof FormData)) {
            headers['Content-Type'] = headers['Content-Type'] || 'application/json';
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        // Handle 401 - session expired
        if (response.status === 401) {
            Auth.clearSession();
            window.location.reload();
            throw new Error('Sessione scaduta');
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.error || errorData.detail ||
                Object.values(errorData).flat().join(', ') ||
                'Errore del server';
            throw new Error(errorMsg);
        }

        // Handle 204 No Content
        if (response.status === 204) return null;

        return response.json();
    },

    // === MACHINES ===
    async getMachines(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.request(`/machines/${query ? '?' + query : ''}`);
    },

    async getMachine(id) {
        return this.request(`/machines/${id}/`);
    },

    async createMachine(data) {
        return this.request('/machines/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    async updateMachine(id, data) {
        return this.request(`/machines/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },

    async deleteMachine(id) {
        return this.request(`/machines/${id}/`, { method: 'DELETE' });
    },

    async getMachineStats() {
        return this.request('/machines/stats/');
    },

    async getLiveStatus() {
        return this.request('/machines/live_status/');
    },

    async getStatusLogs(machineId) {
        return this.request(`/machines/${machineId}/status_logs/`);
    },

    // === IT DATA ===
    async getITData(machineId) {
        return this.request(`/machines/${machineId}/it-data/`);
    },

    async updateITData(machineId, data) {
        return this.request(`/machines/${machineId}/it-data/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },

    // === TECH DATA ===
    async getTechData(machineId) {
        return this.request(`/machines/${machineId}/tech-data/`);
    },

    async updateTechData(machineId, data) {
        return this.request(`/machines/${machineId}/tech-data/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    },

    // === DOCUMENTS ===
    async getDocuments(machineId) {
        return this.request(`/machines/${machineId}/documents/`);
    },

    async uploadDocument(machineId, formData) {
        return this.request(`/machines/${machineId}/documents/`, {
            method: 'POST',
            body: formData,
        });
    },

    async deleteDocument(machineId, docId) {
        return this.request(`/machines/${machineId}/documents/${docId}/`, {
            method: 'DELETE',
        });
    },

    // === ADMIN DOCUMENTS ===
    async getAdminDocuments(machineId) {
        return this.request(`/machines/${machineId}/admin-documents/`);
    },

    async uploadAdminDocument(machineId, formData) {
        return this.request(`/machines/${machineId}/admin-documents/`, {
            method: 'POST',
            body: formData,
        });
    },

    async deleteAdminDocument(machineId, docId) {
        return this.request(`/machines/${machineId}/admin-documents/${docId}/`, {
            method: 'DELETE',
        });
    },
};
