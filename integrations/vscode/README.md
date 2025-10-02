# DJP Workflow VS Code Extension

Lightweight VS Code extension for running DJP templates and workflows directly from the editor.

## Features

- **Run Template on Selection** - Render a template with selected text as input
- **Quick Brief** - Triage selected content via DJP workflow

## Prerequisites

- VS Code 1.75+
- DJP web API running on `http://localhost:8000` (configurable)

## Installation

### Local Install (Development)

```bash
cd integrations/vscode/extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Package extension (optional)
npx vsce package

# Install in VS Code
# Method 1: Press F5 in VS Code to launch Extension Development Host
# Method 2: Extensions → Install from VSIX → select djp-workflow-1.0.0.vsix
```

## Usage

### Run Template on Selection

1. Select text in editor
2. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
3. Run command: **DJP: Run Template on Selection**
4. Choose template from list
5. Fill in required inputs
6. View preview in side panel
7. Artifact saved to `runs/api/`

### Quick Brief

1. Select text in editor
2. Open Command Palette
3. Run command: **DJP: Quick Brief**
4. View analysis in side panel
5. Artifact ID shown in notification

## Configuration

Settings available in VS Code preferences:

```json
{
  "djp.webApiBase": "http://localhost:8000",
  "djp.artifactsDir": "runs/"
}
```

## Development

```bash
# Watch mode for development
npm run watch

# Lint code
npm run lint
```

## Troubleshooting

### "No templates available"
- Ensure web API is running: `uvicorn src.webapi:app --port 8000`
- Check `djp.webApiBase` setting matches API URL

### "Failed to render template"
- Verify all required inputs filled
- Check API logs for errors

### Extension not loading
- Check VS Code extension host logs: Help → Toggle Developer Tools → Console
- Ensure TypeScript compiled: `npm run compile`

## Security Notes

- Extension connects to local API only by default
- Configure `djp.webApiBase` carefully in production
- No credentials stored in extension
- Uses VS Code's fetch API (respects proxy settings)

## Production Deployment

For production use:

1. Update `djp.webApiBase` to cloud API URL (e.g., `https://djp.example.com`)
2. Add authentication headers if required (modify `extension.ts`)
3. Package extension: `npx vsce package`
4. Distribute VSIX or publish to marketplace

## Next Steps

- [ ] Add authentication support
- [ ] Support template favorites
- [ ] Add keyboard shortcuts
- [ ] Publish to VS Code Marketplace
