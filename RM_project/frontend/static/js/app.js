// Questo file avvia l'applicazione frontend e gestisce il flusso di login/logout.

/**
 * app.js — Entry point, routing e inizializzazione
 */

(function () {
    'use strict';

    const loginScreen = document.getElementById('login-screen');
    const appScreen = document.getElementById('app');
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const loginBtn = document.getElementById('login-btn');
    const logoutBtn = document.getElementById('logout-btn');

    // === VERIFICA STATO AUTENTICAZIONE ===
    function checkAuth() {
        if (Auth.isAuthenticated()) {
            showApp();
        } else {
            showLogin();
        }
    }

    function showLogin() {
        loginScreen.style.display = 'flex';
        appScreen.style.display = 'none';
        Dashboard.stopPolling();
    }

    function showApp() {
        loginScreen.style.display = 'none';
        appScreen.style.display = 'flex';
        Dashboard.init();
    }

    // === ACCESSO ===
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;

        // Mostra il caricamento
        loginBtn.querySelector('.btn-text').style.display = 'none';
        loginBtn.querySelector('.btn-loader').style.display = 'inline-flex';
        loginBtn.disabled = true;
        loginError.style.display = 'none';

        try {
            await Auth.login(username, password);
            showApp();
        } catch (err) {
            loginError.textContent = err.message;
            loginError.style.display = 'block';

            // Animazione di vibrazione
            loginError.style.animation = 'none';
            loginError.offsetHeight; // Trigger reflow
            loginError.style.animation = 'fadeIn 0.3s ease';
        } finally {
            loginBtn.querySelector('.btn-text').style.display = 'inline';
            loginBtn.querySelector('.btn-loader').style.display = 'none';
            loginBtn.disabled = false;
        }
    });

    // === DISCONNESSIONE ===
    logoutBtn.addEventListener('click', () => {
        Auth.logout();
        showLogin();
        Components.toast('Logout effettuato.', 'info');

        // Reimposta il form
        loginForm.reset();
        loginError.style.display = 'none';
    });

    // === INIZIALIZZAZIONE ===
    checkAuth();
})();
