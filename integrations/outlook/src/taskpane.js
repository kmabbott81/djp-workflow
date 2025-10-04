/* global Office */

const API_BASE = 'http://localhost:8000/api';
let templates = [];
let selectedTemplate = null;

Office.initialize = function () {
    loadTemplates();
};

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/templates`);
        templates = await response.json();
        console.log('Templates loaded:', templates.length);
    } catch (error) {
        showStatus('Failed to load templates: ' + error.message, 'error');
    }
}

function showTemplateForm() {
    document.getElementById('templateForm').style.display = 'block';
    const select = document.getElementById('templateSelect');
    select.innerHTML = '<option value="">-- Select Template --</option>';

    templates.forEach((template, index) => {
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${template.name} (v${template.version})`;
        select.appendChild(option);
    });
}

function cancelTemplate() {
    document.getElementById('templateForm').style.display = 'none';
    document.getElementById('inputFields').innerHTML = '';
}

function loadTemplateInputs() {
    const select = document.getElementById('templateSelect');
    const index = select.value;

    if (index === '') {
        document.getElementById('inputFields').innerHTML = '';
        return;
    }

    selectedTemplate = templates[index];
    const container = document.getElementById('inputFields');
    container.innerHTML = '';

    selectedTemplate.inputs.forEach(input => {
        const label = document.createElement('label');
        label.textContent = input.label + (input.required ? ' *' : '');

        let field;
        if (input.type === 'enum') {
            field = document.createElement('select');
            field.id = 'input_' + input.id;
            input.enum.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option;
                opt.textContent = option;
                field.appendChild(opt);
            });
        } else if (input.type === 'text') {
            field = document.createElement('textarea');
            field.id = 'input_' + input.id;
        } else {
            field = document.createElement('input');
            field.id = 'input_' + input.id;
            field.type = input.type === 'integer' ? 'number' : 'text';
        }

        field.required = input.required;

        container.appendChild(label);
        container.appendChild(field);
    });
}

async function renderAndInsert() {
    if (!selectedTemplate) {
        showStatus('Please select a template', 'error');
        return;
    }

    // Collect input values
    const inputs = {};
    selectedTemplate.inputs.forEach(input => {
        const field = document.getElementById('input_' + input.id);
        inputs[input.id] = field.value;
    });

    try {
        showStatus('Rendering template...', 'success');

        const response = await fetch(`${API_BASE}/render`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                template_name: selectedTemplate.name,
                inputs: inputs,
                output_format: 'html'
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Rendering failed');
        }

        // Insert into email body
        Office.context.mailbox.item.body.setAsync(
            result.html,
            { coercionType: Office.CoercionType.Html },
            function (asyncResult) {
                if (asyncResult.status === Office.AsyncResultStatus.Failed) {
                    showStatus('Failed to insert content: ' + asyncResult.error.message, 'error');
                } else {
                    showStatus('Content inserted successfully!', 'success');
                    cancelTemplate();
                }
            }
        );

    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

async function triageEmail() {
    try {
        showStatus('Sending to DJP triage...', 'success');

        Office.context.mailbox.item.body.getAsync(
            Office.CoercionType.Text,
            async function (asyncResult) {
                if (asyncResult.status === Office.AsyncResultStatus.Failed) {
                    showStatus('Failed to read email: ' + asyncResult.error.message, 'error');
                    return;
                }

                const content = asyncResult.value;
                const subject = Office.context.mailbox.item.subject;

                const response = await fetch(`${API_BASE}/triage`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: content,
                        subject: subject
                    })
                });

                const result = await response.json();

                if (!result.success) {
                    throw new Error(result.error || 'Triage failed');
                }

                showStatus(`Triage complete! Artifact: ${result.artifact_id}`, 'success');
            }
        );

    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.textContent = message;
    status.className = type;
    status.style.display = 'block';

    setTimeout(() => {
        status.style.display = 'none';
    }, 5000);
}
