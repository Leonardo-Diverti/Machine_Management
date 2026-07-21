// Questo file gestisce l'autenticazione JWT e la sessione utente nel browser.

/**
 * auth.js — Gestione autenticazione JWT
 */

const Auth = {
    TOKEN_KEY: 'mh_access_token',
    REFRESH_KEY: 'mh_refresh_token',
    USER_KEY: 'mh_user',

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    getRefreshToken() {
        return localStorage.getItem(this.REFRESH_KEY);
    },

    getUser() {
        const data = localStorage.getItem(this.USER_KEY);
        return data ? JSON.parse(data) : null;
    },

    setSession(data) {
        localStorage.setItem(this.TOKEN_KEY, data.access);
        localStorage.setItem(this.REFRESH_KEY, data.refresh);
        localStorage.setItem(this.USER_KEY, JSON.stringify(data.user));
    },

    clearSession() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_KEY);
        localStorage.removeItem(this.USER_KEY);
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    getUserOffice() {
        const user = this.getUser();
        if (user && user.profile && user.profile.office) {
            return user.profile.office;
        }
        return null;
    },

    getUserPermissions() {
        const user = this.getUser();
        if (user && user.profile && user.profile.permissions) {
            return user.profile.permissions;
        }
        return {};
    },

    canWrite(modelName, fieldName) {
        const user = this.getUser();
        if (!user) return false;

        const perms = this.getUserPermissions();
        if (!perms[modelName]) return false;

        // Controlla il carattere jolly
        if (perms[modelName]['*'] === 'WRITE') return true;

        return perms[modelName][fieldName] === 'WRITE';
    },

    canRead(modelName, fieldName) {
        const perms = this.getUserPermissions();
        if (!perms[modelName]) return false;

        if (perms[modelName]['*']) return true;

        return !!perms[modelName][fieldName];
    },

    hasAnyPermission(modelName) {
        const perms = this.getUserPermissions();
        return !!perms[modelName];
    },

    async login(username, password) {
        const response = await fetch('/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Errore di autenticazione');
        }

        this.setSession(data);
        return data;
    },

    async refreshUserData() {
        const response = await fetch('/api/auth/me/', {
            headers: {
                'Authorization': `Bearer ${this.getToken()}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            const userData = await response.json();
            const user = this.getUser();
            // Unisce i permessi dal profilo
            localStorage.setItem(this.USER_KEY, JSON.stringify(userData));
            return userData;
        }
        return null;
    },

    logout() {
        const refreshToken = this.getRefreshToken();
        if (refreshToken) {
            fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.getToken()}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
            }).catch(() => {});
        }
        this.clearSession();
    }
};
