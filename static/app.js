var currentUsername = null;
const characterLimit = 5000;
const contentTextarea = document.getElementById('content');
const charCount = document.getElementById('charCount');
const submitButton = document.getElementById('submitButton');
const submissionStatus = document.getElementById('submissionStatus');
const resultDiv = document.getElementById('result');
const copyLinkButton = document.getElementById('copyLinkButton');


async function post(endpoint, params, headers = {}) {
  let ref = window.location.href;
  return fetch((ref.endsWith('/') ? ref.slice(0, -1) : ref) + endpoint, {
    credentials: 'include',
    body: params,
    headers: headers || {'Content-Type': 'application/x-www-form-urlencoded',},
    method: 'POST',
  });
}

function showStatus(message, type) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    statusEl.classList.remove('hidden');
    setTimeout(() => {  // Hide after 10 seconds
        statusEl.classList.add('hidden');
    }, 10000);
}

function showPastebin() {
    const authSection = document.getElementById('authSection');
    authSection.className = `container container-sm hidden`;
    const pasteSection = document.getElementById('pasteSection');
    pasteSection.classList.remove('hidden');
    const usernameEl = document.getElementById('userName');
    usernameEl.textContent = currentUsername;
}

function hidePastebin() {
    const authSection = document.getElementById('authSection');
    authSection.classList.remove('hidden');
    const pasteSection = document.getElementById('pasteSection');
    pasteSection.className = `container container-lg hidden`;
    const usernameEl = document.getElementById('userName');
    usernameEl.textContent = '';
}

async function registerUsername() {
    let params = new URLSearchParams();
    let username = document.getElementById('registerUsername').value;
    if (!username) {
        showStatus('Please enter a username', 'error');
        return;
    }
    params.append('username', username);
    let password = document.getElementById('registerPassword').value;
    if (!password) {
        showStatus('Please enter a password', 'error');
        return;
    }
    params.append('password', password);
    showStatus('Registering username ' + username + '...', 'info');
    let response = await post('/api/register', params);
    let data = {};
    if (response.headers.get('Content-Type') === 'application/json') {
        data = await response.json();
    }
    if (!response.ok) {
        const message = data?.error || 'unknown error';
        showStatus(`Failed to register: ${message}`, 'error');
        throw new Error(message);
    } else {
        username = data.username || 'unknown';
        showStatus('Successfully registered user ' + username + '!', 'success');
        showTab('login');
    }
}

async function authenticateUsername() {
    let params = new URLSearchParams();
    let username = document.getElementById('loginUsername').value;
    if (!username) {
        showStatus('Please enter a username', 'error');
        return;
    }
    params.append('username', username);
    let password = document.getElementById('loginPassword').value;
    if (!password) {
        showStatus('Please enter a password', 'error');
        return;
    }
    params.append('password', password);
    showStatus('Authenticating ' + username + '...', 'info');
    let response = await post('/api/login', params);
    let data = {};
    if (response.headers.get('Content-Type') === 'application/json') {
        data = await response.json();
    }
    if (!response.ok) {
        const message = data?.error || 'unknown error';
        showStatus(`Failed to login: ${message}`, 'error');
        throw new Error(message);
    } else {
        currentUsername = data.username || 'Unknown';
        showStatus('Successfully logged in!', 'success');
        showPastebin();
    }
}

async function createPaste() {
    submissionStatus.className = `result-item hidden`;
    resultDiv.textContent = '';
    resultDiv.className = 'result';
    copyLinkButton.className = 'button-copy hidden';
    const content = contentTextarea.value.trim();
    if (!content) {
        showResult('Please enter some text', 'error');
        return;
    }
    if (content.length > characterLimit) {
        showResult('Text exceeds 500 character limit', 'error');
        return;
    }
    submitButton.disabled = true;
    submitButton.textContent = 'Creating...';
    let hadFailed = false;
    try {
        const response = await post('/api/paste', JSON.stringify({ text: content }), {'Content-Type': 'application/json',});
        const data = await response.json();
        if (response.ok) {
            const origin = window.location.origin;
            const pathname = window.location.pathname;
            const pasteUrl = `${origin}${pathname}paste/${data.id}`;
            showResult(pasteUrl, 'success url');
            copyLinkButton.classList.remove('hidden');
            contentTextarea.value = '';
            updateCharCount();
        } else {
            showResult(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        hadFailed = true;
        showResult('Network error. Please try again.', 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = `Create${hadFailed ? ' ' : ' New '}Paste`;
    }
}

function showResult(message, type) {
    submissionStatus.classList.remove('hidden');
    resultDiv.textContent = message;
    resultDiv.className = `result ${type}`;
    resultDiv.style.display = 'block';
}

function copyLink() {
    const url = document.querySelector('.url').textContent;
    navigator.clipboard.writeText(url);
    showResult('Link copied to clipboard!', 'success');
    setTimeout(() => showResult(url, 'success url'), 5000);
}

async function register() {
  try {
    await registerUsername();
  } catch (error) {
      console.error("Registration failed:", error);
  }
}

async function authenticate() {
  try {
    await authenticateUsername();
  } catch(error) {
      console.error("Authentication failed:", error);
  }
}

function showTab(tabName) {
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    const clickedButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if(clickedButton) {
        clickedButton.classList.add('active');
    }
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

function logout() {
    showStatus('Logging out...', 'info');
    post('/api/logout')
        .then(() => {
            hidePastebin();
            currentUsername = null;
            showStatus('Successfully logged out!', 'success');
        })
        .catch(() => {
            showStatus('Failed to logout', 'error');
        });
}

function updateCharCount () {
    if (contentTextarea == null) return;
    const length = contentTextarea.value.length;
    charCount.textContent = `${length}/${characterLimit} characters`;
    if (length > characterLimit) {
        charCount.classList.add('warning');
        submitButton.disabled = true;
    } else {
        charCount.classList.remove('warning');
        submitButton.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Attach event listeners to forms
    const registerForm = document.getElementById('registerForm');
    if(registerForm) {
        registerForm.addEventListener('submit', (e) => {
            e.preventDefault();
            register();
        });
    }

    const loginForm = document.getElementById('loginForm');
    if(loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            authenticate();
        });
    }

    if (contentTextarea != null) {
        contentTextarea.addEventListener('input', updateCharCount);
    }
    updateCharCount();
});

