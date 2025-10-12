// Action Runner - Dev Preview Client
// Sprint 55 Week 3

const API_BASE = '';  // Same origin
const DEMO_WORKSPACE_ID = 'demo-workspace-001';
let availableActions = [];
let currentPreviewId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadActions();
    await loadOutbox();
    setupEventListeners();
    showBanner();
});

// Load available actions from API
async function loadActions() {
    try {
        const response = await fetch(`${API_BASE}/actions`);
        const data = await response.json();

        availableActions = data.actions || [];

        const select = document.getElementById('actionSelect');
        select.innerHTML = '<option value="">-- Select an action --</option>';

        availableActions.forEach(action => {
            const option = document.createElement('option');
            option.value = action.id;
            option.textContent = `${action.id} - ${action.description || ''}`;
            select.appendChild(option);
        });

        // Pre-select gmail.send if available
        if (availableActions.some(a => a.id === 'gmail.send')) {
            select.value = 'gmail.send';
            await checkOAuthStatus('gmail');
        }
    } catch (error) {
        showResult(`Error loading actions: ${error.message}`, true);
    }
}

// Check OAuth status for provider
async function checkOAuthStatus(provider) {
    const statusDiv = document.getElementById('oauthStatus');

    try {
        const response = await fetch(`${API_BASE}/oauth/${provider}/status?workspace_id=${DEMO_WORKSPACE_ID}`);
        const data = await response.json();

        if (data.linked) {
            statusDiv.innerHTML = `
                <div class="oauth-status">
                    <span class="dot connected"></span>
                    <span>${provider.toUpperCase()} Connected - Scopes: ${data.scopes || 'unknown'}</span>
                </div>
            `;
        } else {
            statusDiv.innerHTML = `
                <div class="oauth-status">
                    <span class="dot"></span>
                    <span>${provider.toUpperCase()} Not Connected - Using Demo Mode</span>
                </div>
            `;
        }
    } catch (error) {
        statusDiv.innerHTML = `
            <div class="oauth-status">
                <span class="dot"></span>
                <span>${provider.toUpperCase()} Status Unknown - Demo Mode Available</span>
            </div>
        `;
    }
}

// Show banner with feature flag info
function showBanner() {
    const container = document.getElementById('bannerContainer');
    container.innerHTML = `
        <div class="banner">
            <strong>Dev Mode:</strong> Preview emails before sending, or use demo mode to save to local outbox without actual sends.
        </div>
    `;
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('actionSelect').addEventListener('change', async (e) => {
        const actionId = e.target.value;
        if (actionId.startsWith('gmail.')) {
            await checkOAuthStatus('gmail');
        } else if (actionId.startsWith('outlook.')) {
            await checkOAuthStatus('microsoft');
        }
    });

    document.getElementById('previewBtn').addEventListener('click', handlePreview);
    document.getElementById('executeBtn').addEventListener('click', handleExecute);
    document.getElementById('refreshOutboxBtn').addEventListener('click', loadOutbox);
}

// Handle preview button
async function handlePreview() {
    const btn = document.getElementById('previewBtn');
    const resultBox = document.getElementById('resultBox');
    const previewCard = document.getElementById('previewCard');
    const previewContent = document.getElementById('previewContent');

    try {
        btn.disabled = true;
        btn.innerHTML = 'Previewing...<span class="loading"></span>';
        resultBox.style.display = 'none';

        const params = await buildEmailParams();
        const actionId = document.getElementById('actionSelect').value;

        if (!actionId) {
            throw new Error('Please select an action');
        }

        const response = await fetch(`${API_BASE}/actions/preview`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer relay_sk_demo_preview_key'
            },
            body: JSON.stringify({
                action: actionId,
                params
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Preview failed');
        }

        const result = await response.json();
        currentPreviewId = result.preview_id;

        // Show preview
        previewCard.style.display = 'block';

        // Render preview (sanitized HTML in iframe)
        const htmlBody = params.body || params.html_body || '';
        const previewHTML = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; padding: 20px; }
                    pre { background: #f5f7fa; padding: 10px; border-radius: 4px; }
                </style>
            </head>
            <body>
                <h3>Subject: ${params.subject || '(no subject)'}</h3>
                <p><strong>To:</strong> ${params.to || ''}</p>
                ${params.cc ? `<p><strong>Cc:</strong> ${params.cc}</p>` : ''}
                ${params.bcc ? `<p><strong>Bcc:</strong> ${params.bcc}</p>` : ''}
                <hr>
                <div>${htmlBody}</div>
            </body>
            </html>
        `;

        const iframe = document.createElement('iframe');
        iframe.sandbox = 'allow-same-origin';
        iframe.srcdoc = previewHTML;
        previewContent.innerHTML = '';
        previewContent.appendChild(iframe);

        showResult(`Preview created successfully. Preview ID: ${result.preview_id}`, false);

    } catch (error) {
        showResult(`Preview error: ${error.message}`, true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Preview';
    }
}

// Handle execute button (demo mode)
async function handleExecute() {
    const btn = document.getElementById('executeBtn');
    const resultBox = document.getElementById('resultBox');

    try {
        btn.disabled = true;
        btn.innerHTML = 'Executing (Demo)...<span class="loading"></span>';
        resultBox.style.display = 'none';

        const params = await buildEmailParams();
        const actionId = document.getElementById('actionSelect').value;

        if (!actionId) {
            throw new Error('Please select an action');
        }

        // Save to demo outbox instead of actually sending
        await saveToDemoOutbox(actionId, params);

        showResult('✅ Email saved to demo outbox (not actually sent)', false);
        await loadOutbox();

    } catch (error) {
        showResult(`Execute error: ${error.message}`, true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Execute (Demo Mode)';
    }
}

// Save email to demo outbox
async function saveToDemoOutbox(actionId, params) {
    const timestamp = new Date().toISOString();
    const outboxItem = {
        id: `demo-${Date.now()}`,
        action: actionId,
        params,
        timestamp,
        mode: 'demo',
        status: 'saved'
    };

    // In a real implementation, this would POST to /dev/outbox
    // For now, we'll use localStorage
    const outbox = JSON.parse(localStorage.getItem('demoOutbox') || '[]');
    outbox.unshift(outboxItem);

    // Keep only last 20 items
    if (outbox.length > 20) {
        outbox.splice(20);
    }

    localStorage.setItem('demoOutbox', JSON.stringify(outbox));
}

// Load demo outbox
async function loadOutbox() {
    const content = document.getElementById('outboxContent');

    try {
        // Try to load from server first
        try {
            const response = await fetch(`${API_BASE}/dev/outbox`);
            if (response.ok) {
                const data = await response.json();
                if (data.items && data.items.length > 0) {
                    renderOutbox(data.items);
                    return;
                }
            }
        } catch (e) {
            // Fallback to localStorage
        }

        // Load from localStorage
        const outbox = JSON.parse(localStorage.getItem('demoOutbox') || '[]');
        renderOutbox(outbox);

    } catch (error) {
        content.innerHTML = `<p style="color: #e53e3e;">Error loading outbox: ${error.message}</p>`;
    }
}

// Render outbox items
function renderOutbox(items) {
    const content = document.getElementById('outboxContent');

    if (items.length === 0) {
        content.innerHTML = '<p style="color: #718096;">No demo emails yet. Execute an action to see items here.</p>';
        return;
    }

    content.innerHTML = items.map((item, idx) => `
        <div class="outbox-item">
            <div class="meta">${new Date(item.timestamp).toLocaleString()} - ${item.action}</div>
            <div><strong>To:</strong> ${item.params?.to || '(none)'}</div>
            <div><strong>Subject:</strong> ${item.params?.subject || '(none)'}</div>
            <div><strong>Status:</strong> ${item.status || 'saved'}</div>
        </div>
    `).join('');
}

// Build email params from form
async function buildEmailParams() {
    const to = document.getElementById('recipientTo').value.trim();
    const cc = document.getElementById('recipientCc').value.trim();
    const bcc = document.getElementById('recipientBcc').value.trim();
    const subject = document.getElementById('emailSubject').value.trim();
    const body = document.getElementById('emailBody').value.trim();
    const attachmentInput = document.getElementById('attachmentInput');

    const params = {
        to,
        subject,
        body: body || '<p>Test email from Action Runner</p>'
    };

    if (cc) {
        params.cc = cc;
    }

    if (bcc) {
        params.bcc = bcc;
    }

    // Handle attachments (base64 encode in browser)
    if (attachmentInput.files.length > 0) {
        const attachments = [];

        for (let i = 0; i < attachmentInput.files.length; i++) {
            const file = attachmentInput.files[i];
            const base64 = await fileToBase64(file);

            attachments.push({
                filename: file.name,
                content: base64.split(',')[1],  // Remove data:... prefix
                content_type: file.type || 'application/octet-stream',
                size: file.size
            });
        }

        params.attachments = attachments;
    }

    return params;
}

// Convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Show result message
function showResult(message, isError) {
    const resultBox = document.getElementById('resultBox');
    resultBox.className = isError ? 'result-box error' : 'result-box';
    resultBox.innerHTML = `<pre>${message}</pre>`;
    resultBox.style.display = 'block';
}
