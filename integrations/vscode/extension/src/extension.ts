import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
    console.log('DJP Workflow extension activated');

    // Register Run Template command
    let runTemplate = vscode.commands.registerCommand('djp.runTemplate', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const selection = editor.document.getText(editor.selection);
        if (!selection) {
            vscode.window.showWarningMessage('No text selected');
            return;
        }

        await runTemplateOnSelection(selection);
    });

    // Register Quick Brief command
    let quickBrief = vscode.commands.registerCommand('djp.quickBrief', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        const selection = editor.document.getText(editor.selection);
        if (!selection) {
            vscode.window.showWarningMessage('No text selected');
            return;
        }

        await quickBriefSelection(selection);
    });

    context.subscriptions.push(runTemplate, quickBrief);
}

async function runTemplateOnSelection(text: string) {
    const config = vscode.workspace.getConfiguration('djp');
    const apiBase = config.get<string>('webApiBase', 'http://localhost:8000');

    try {
        // Fetch templates
        const templatesResponse = await fetch(`${apiBase}/api/templates`);
        const templates = await templatesResponse.json();

        if (templates.length === 0) {
            vscode.window.showErrorMessage('No templates available');
            return;
        }

        // Show template picker
        const templateNames = templates.map((t: any) => `${t.name} (v${t.version})`);
        const selected = await vscode.window.showQuickPick(templateNames, {
            placeHolder: 'Select a template'
        });

        if (!selected) {
            return;
        }

        const templateIndex = templateNames.indexOf(selected);
        const template = templates[templateIndex];

        // Collect inputs
        const inputs: any = {};
        for (const input of template.inputs) {
            if (input.type === 'enum') {
                const value = await vscode.window.showQuickPick(input.enum, {
                    placeHolder: input.label
                });
                if (!value) return;
                inputs[input.id] = value;
            } else if (input.type === 'text') {
                const value = await vscode.window.showInputBox({
                    prompt: input.label,
                    value: text,
                    validateInput: (value) => {
                        return input.required && !value ? 'This field is required' : null;
                    }
                });
                if (value === undefined) return;
                inputs[input.id] = value;
            } else {
                const value = await vscode.window.showInputBox({
                    prompt: input.label,
                    validateInput: (value) => {
                        return input.required && !value ? 'This field is required' : null;
                    }
                });
                if (value === undefined) return;
                inputs[input.id] = value;
            }
        }

        // Render template
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Rendering template...',
            cancellable: false
        }, async () => {
            const renderResponse = await fetch(`${apiBase}/api/render`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_name: template.name,
                    inputs: inputs,
                    output_format: 'html'
                })
            });

            const result = await renderResponse.json();

            if (!result.success) {
                throw new Error(result.error || 'Rendering failed');
            }

            // Show preview
            const panel = vscode.window.createWebviewPanel(
                'djpPreview',
                `Preview: ${template.name}`,
                vscode.ViewColumn.Beside,
                { enableScripts: true }
            );

            panel.webview.html = result.html;

            // Save artifact
            const artifactsDir = config.get<string>('artifactsDir', 'runs/');
            const artifactPath = path.join(artifactsDir, path.basename(result.artifact_path));

            vscode.window.showInformationMessage(`Template rendered! Artifact: ${artifactPath}`);
        });

    } catch (error: any) {
        vscode.window.showErrorMessage(`Error: ${error.message}`);
    }
}

async function quickBriefSelection(text: string) {
    const config = vscode.workspace.getConfiguration('djp');
    const apiBase = config.get<string>('webApiBase', 'http://localhost:8000');

    try {
        await vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Running DJP triage...',
            cancellable: false
        }, async () => {
            const triageResponse = await fetch(`${apiBase}/api/triage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: text,
                    subject: 'Quick Brief from VS Code'
                })
            });

            const result = await triageResponse.json();

            if (!result.success) {
                throw new Error(result.error || 'Triage failed');
            }

            // Show result in webview
            const panel = vscode.window.createWebviewPanel(
                'djpBrief',
                `Quick Brief: ${result.artifact_id}`,
                vscode.ViewColumn.Beside,
                {}
            );

            panel.webview.html = `
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        h2 { color: #333; }
                        .meta { color: #666; font-size: 0.9em; margin-bottom: 20px; }
                        .preview { background: #f5f5f5; padding: 15px; border-radius: 4px; }
                    </style>
                </head>
                <body>
                    <h2>Quick Brief Result</h2>
                    <div class="meta">
                        <strong>Artifact ID:</strong> ${result.artifact_id}<br>
                        <strong>Provider:</strong> ${result.provider}<br>
                        <strong>Status:</strong> ${result.status}
                    </div>
                    <div class="preview">
                        <strong>Preview:</strong><br><br>
                        ${result.preview.replace(/\n/g, '<br>')}
                    </div>
                </body>
                </html>
            `;

            vscode.window.showInformationMessage(`Brief complete! Artifact: ${result.artifact_id}`);
        });

    } catch (error: any) {
        vscode.window.showErrorMessage(`Error: ${error.message}`);
    }
}

export function deactivate() {}
