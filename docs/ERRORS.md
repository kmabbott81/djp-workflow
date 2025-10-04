# Error Reference Guide

Comprehensive guide to common errors, their causes, resolutions, and prevention strategies.

## Table of Contents

- [API Key Errors](#api-key-errors)
- [Connection and Timeout Errors](#connection-and-timeout-errors)
- [Rate Limiting and Quota Errors](#rate-limiting-and-quota-errors)
- [Template Errors](#template-errors)
- [File System Errors](#file-system-errors)
- [Validation Errors](#validation-errors)
- [Windows-Specific Issues](#windows-specific-issues)

## API Key Errors

### Error: "OPENAI_API_KEY not found"

**Symptom:**
```
Error: OPENAI_API_KEY environment variable not set
```

**Cause:**
Environment variable not configured or not visible to the application.

**Resolution:**

Windows (PowerShell):
```powershell
# Set for current session
$env:OPENAI_API_KEY = "sk-proj-your-key-here"

# Verify
echo $env:OPENAI_API_KEY

# Run workflow
python -m src.run_workflow --task "Test question"
```

Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=sk-proj-your-key-here
python -m src.run_workflow --task "Test question"
```

macOS/Linux:
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
python -m src.run_workflow --task "Test question"
```

Best practice - Use `.env.local` file:
```bash
# Create .env.local (git-ignored)
echo "OPENAI_API_KEY=sk-proj-your-key-here" > .env.local
```

**Prevention:**
- Use `.env.local` file for persistent configuration
- Add `.env.local` to `.gitignore` (already configured)
- Verify with: `python -c "import os; print(bool(os.getenv('OPENAI_API_KEY')))"`

---

### Error: "Invalid API key format"

**Symptom:**
```
AuthenticationError: Invalid API key provided
Status code: 401
```

**Cause:**
- API key has incorrect format
- Key contains spaces or hidden characters
- Using expired or revoked key
- Wrong key type (e.g., project key vs user key)

**Resolution:**

1. Verify key format:
   - Modern keys: Start with `sk-proj-`
   - Legacy keys: Start with `sk-`
   - Must be alphanumeric with hyphens

2. Check for hidden characters:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY.Trim()

# macOS/Linux
echo "$OPENAI_API_KEY" | cat -A  # Shows hidden chars
```

3. Generate new key:
   - Visit https://platform.openai.com/api-keys
   - Create new key
   - Copy entire key (no spaces)
   - Update `.env.local`

**Prevention:**
- Copy keys directly from OpenAI dashboard
- Use password manager for secure storage
- Test immediately after setting: `python -c "import openai; print('Key valid')"`

---

### Error: "Incorrect API key provided"

**Symptom:**
```
AuthenticationError: Incorrect API key provided
You can find your API key at https://platform.openai.com/account/api-keys
```

**Cause:**
- Key has been revoked or deleted
- Using key from wrong OpenAI account
- Key has expired

**Resolution:**

1. Verify key status at https://platform.openai.com/api-keys
2. Check if key is active (not revoked)
3. Generate new key if needed
4. Update environment variable

**Prevention:**
- Rotate keys every 90 days
- Monitor key usage in OpenAI dashboard
- Use separate keys for dev/staging/prod
- Document key creation dates

---

## Connection and Timeout Errors

### Error: "Connection timeout"

**Symptom:**
```
ConnectTimeout: Connection to api.openai.com timed out after 10000ms
```

**Cause:**
- Network connectivity issues
- Firewall blocking outbound connections
- VPN or proxy interference
- OpenAI API experiencing issues

**Resolution:**

1. Increase timeout:
```bash
# In .env.local
OPENAI_CONNECT_TIMEOUT_MS=30000
OPENAI_READ_TIMEOUT_MS=120000
```

2. Test network connectivity:
```bash
# Windows
ping api.openai.com
curl -I https://api.openai.com/v1/models

# macOS/Linux
ping api.openai.com
curl -I https://api.openai.com/v1/models
```

3. Check firewall settings:
```bash
# Windows: Ensure outbound HTTPS (443) allowed
# macOS: Check System Preferences → Security & Privacy → Firewall
# Linux: Check iptables or ufw rules
```

4. Disable VPN temporarily to test

**Prevention:**
- Set generous timeouts for production
- Monitor network latency
- Use retry logic with exponential backoff
- Check OpenAI status page: https://status.openai.com

---

### Error: "Read timeout"

**Symptom:**
```
ReadTimeout: Request to api.openai.com timed out after 60000ms while reading response
```

**Cause:**
- Large response taking too long
- Complex workflow exceeding timeout
- Network congestion
- API processing delay

**Resolution:**

1. Increase read timeout:
```bash
# In .env.local
OPENAI_READ_TIMEOUT_MS=180000  # 3 minutes
```

2. Reduce complexity:
```bash
# Lower max_tokens
python -m src.run_workflow --task "Question" --max_tokens 500

# Use faster model
python -m src.run_workflow --task "Question" --model gpt-4o-mini
```

3. Use streaming for long responses (if supported)

**Prevention:**
- Set read timeout to 2-3x expected response time
- Use `gpt-4o-mini` for simple tasks
- Limit `max_tokens` appropriately
- Monitor P95 latency in dashboard

---

## Rate Limiting and Quota Errors

### Error: "Rate limit exceeded (429)"

**Symptom:**
```
RateLimitError: Rate limit reached for requests
Status code: 429
Error: You exceeded your current quota, please check your plan and billing details
```

**Cause:**
- Exceeded requests per minute (RPM) limit
- Exceeded tokens per minute (TPM) limit
- Too many concurrent requests
- Insufficient quota/credits

**Resolution:**

1. Implement exponential backoff:
```python
import time
from openai import RateLimitError

max_retries = 3
for attempt in range(max_retries):
    try:
        result = run_workflow(task)
        break
    except RateLimitError:
        wait_time = 2 ** attempt  # 1s, 2s, 4s
        time.sleep(wait_time)
```

2. Check quota and billing:
   - Visit https://platform.openai.com/usage
   - Verify sufficient credits
   - Upgrade plan if needed

3. Reduce request rate:
```bash
# Add delay between requests
python -m src.run_workflow --task "Q1"
sleep 2
python -m src.run_workflow --task "Q2"
```

4. Use tier limits:
   - Free tier: 3 RPM, 40,000 TPM
   - Tier 1: 500 RPM, 100,000 TPM
   - Tier 2+: Higher limits

**Prevention:**
- Implement rate limiting in application
- Use request queuing
- Monitor usage in dashboard
- Set up billing alerts
- Use batch processing for bulk workflows

---

### Error: "Insufficient quota"

**Symptom:**
```
InsufficientQuotaError: You exceeded your current quota
```

**Cause:**
- Free trial expired
- Monthly spending limit reached
- Payment method failed
- Account suspended

**Resolution:**

1. Check billing:
   - Visit https://platform.openai.com/account/billing
   - Verify payment method
   - Add credits if needed

2. Review usage:
   - Check Usage page for cost breakdown
   - Identify expensive workflows
   - Optimize prompts to reduce tokens

3. Set spending limits:
```bash
# Set budget per workflow
python -m src.run_workflow --task "Question" --budget_usd 0.01
```

**Prevention:**
- Set monthly spending limits in OpenAI dashboard
- Use budget guards: `--budget_usd`, `--budget_tokens`
- Monitor costs in observability dashboard
- Use `gpt-4o-mini` for development/testing

---

## Template Errors

### Error: "Template not found"

**Symptom:**
```
FileNotFoundError: Template 'my_template' not found in templates/ or templates/examples/
```

**Cause:**
- Template file doesn't exist
- Wrong template name or path
- Template in wrong directory

**Resolution:**

1. List available templates:
```bash
# Windows
dir /B templates
dir /B templates\examples

# macOS/Linux
ls templates/
ls templates/examples/
```

2. Check template name:
```bash
# Verify exact filename
python -c "
from src.templates import list_templates
templates = list_templates()
for t in templates:
    print(t.workflow_name)
"
```

3. Verify template location:
```bash
# Built-in templates: templates/
# Example templates: templates/examples/
# Custom templates: templates/custom/
```

**Prevention:**
- Use `list_templates()` to get available names
- Store custom templates in `templates/custom/`
- Use tab-completion for template names (if available)

---

### Error: "Template validation failed"

**Symptom:**
```
ValidationError: Template 'my_template.yaml' failed validation:
  - Missing required field: 'prompt_template'
```

**Cause:**
- Invalid YAML syntax
- Missing required fields
- Invalid parameter values
- Schema validation error

**Resolution:**

1. Validate YAML syntax:
```bash
# Install yamllint
pip install yamllint

# Check syntax
yamllint templates/custom/my_template.yaml
```

2. Check required fields:
```yaml
# Minimum required
workflow_name: my_template
description: Brief description
prompt_template: |
  Template content here
```

3. Validate against schema:
```bash
python -c "
from src.templates import load_template
template = load_template('my_template')
print('Template valid')
"
```

**Prevention:**
- Copy from working template
- Use YAML linter in editor
- Test after changes: `load_template('my_template')`
- Keep templates in version control

---

### Error: "Template rendering failed"

**Symptom:**
```
TemplateRenderError: Failed to render template 'my_template':
  - Undefined variable: 'missing_var'
```

**Cause:**
- Missing required variable
- Typo in variable name
- Variable not provided in inputs
- Invalid Jinja2 syntax

**Resolution:**

1. Check variable names:
```yaml
# In template
prompt_template: |
  Context: {context}
  Question: {question}

# Must provide both
python -m src.run_workflow \
  --template my_template \
  --inputs '{"context": "...", "question": "..."}'
```

2. Use default values:
```yaml
prompt_template: |
  Context: {context|default("No context provided")}
```

3. Validate Jinja2 syntax:
```bash
python -c "
from jinja2 import Template
t = Template('Hello {name}')
print(t.render(name='World'))
"
```

**Prevention:**
- Document required variables
- Use default values for optional variables
- Test rendering with dry-run
- Validate inputs before rendering

---

## File System Errors

### Error: "Permission denied writing to logs/"

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'logs/workflow.log'
```

**Cause:**
- Logs directory doesn't exist
- Insufficient write permissions
- File locked by another process
- Antivirus blocking writes

**Resolution:**

Windows:
```powershell
# Create directories
New-Item -ItemType Directory -Force -Path logs, audit, runs

# Grant permissions
icacls logs /grant ${env:USERNAME}:F
icacls audit /grant ${env:USERNAME}:F
icacls runs /grant ${env:USERNAME}:F
```

macOS/Linux:
```bash
# Create directories
mkdir -p logs audit runs

# Grant permissions
chmod 755 logs audit runs
```

**Prevention:**
- Run setup script to create directories
- Verify permissions before first run
- Use writable locations
- Exclude project from antivirus scans

---

### Error: "Artifact directory full"

**Symptom:**
```
IOError: No space left on device
```

**Cause:**
- Disk full
- Too many artifacts accumulated
- Large artifacts not cleaned up

**Resolution:**

1. Check disk space:
```bash
# Windows
wmic logicaldisk get size,freespace,caption

# macOS/Linux
df -h
```

2. Clean old artifacts:
```bash
# Windows
cd runs
del *.json /Q /S

# macOS/Linux
cd runs
find . -name "*.json" -mtime +30 -delete  # Delete >30 days old
```

3. Configure retention:
```bash
# In .env.local
ARTIFACT_RETENTION_DAYS=30
```

**Prevention:**
- Set up artifact retention policy
- Use log rotation
- Monitor disk space
- Archive old artifacts to S3/cloud storage

---

## Validation Errors

### Error: "Schema validation failed"

**Symptom:**
```
ValidationError: Artifact does not conform to schema:
  - 'cost_usd' is required
  - 'published_text' must be string
```

**Cause:**
- Artifact missing required fields
- Field type mismatch
- Schema version incompatibility

**Resolution:**

1. Validate schema:
```bash
python scripts/validate_artifacts.py
```

2. Check artifact structure:
```bash
python -m json.tool runs/2025.10.02-1234.json
```

3. Update to latest schema:
```bash
git pull origin main  # Get latest schemas
```

**Prevention:**
- Use schema validation in CI/CD
- Test artifacts after changes
- Keep schemas versioned
- Document schema changes in CHANGELOG

---

### Error: "Budget exceeded"

**Symptom:**
```
BudgetExceededError: Projected cost $0.015 exceeds budget $0.010
```

**Cause:**
- Workflow exceeds cost budget
- Token usage higher than expected
- Expensive model selected

**Resolution:**

1. Increase budget:
```bash
python -m src.run_workflow --task "Question" --budget_usd 0.02
```

2. Reduce costs:
```bash
# Use cheaper model
python -m src.run_workflow --task "Question" --model gpt-4o-mini

# Reduce tokens
python -m src.run_workflow --task "Question" --max_tokens 500
```

3. Check projected cost:
```bash
python -m src.run_workflow --task "Question" --dry-run
```

**Prevention:**
- Use dry-run mode to check costs first
- Set appropriate budgets: `--budget_usd`, `--budget_tokens`
- Use `gpt-4o-mini` for simple tasks
- Monitor costs in dashboard

---

## Windows-Specific Issues

### Error: "Path contains backslashes causing issues"

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'C:\Users\...'
```

**Cause:**
- Backslashes not escaped
- Path parsing issues
- String literal interpretation

**Resolution:**

1. Use raw strings:
```python
# Bad
path = "C:\Users\kylem\project"

# Good
path = r"C:\Users\kylem\project"  # Raw string
path = "C:\\Users\\kylem\\project"  # Escaped
path = "C:/Users/kylem/project"  # Forward slashes work on Windows
```

2. Use pathlib:
```python
from pathlib import Path
path = Path("C:/Users/kylem/project")
```

3. Use `os.path.join`:
```python
import os
path = os.path.join("C:", "Users", "kylem", "project")
```

**Prevention:**
- Always use raw strings for Windows paths
- Use `pathlib.Path` for cross-platform compatibility
- Avoid hardcoded paths
- Use forward slashes (work on Windows too)

---

### Error: "PowerShell execution policy blocks script"

**Symptom:**
```
.\script.ps1 : File cannot be loaded because running scripts is disabled on this system
```

**Cause:**
- PowerShell execution policy too restrictive
- Default policy blocks unsigned scripts

**Resolution:**

1. Temporarily bypass:
```powershell
powershell -ExecutionPolicy Bypass -File script.ps1
```

2. Set execution policy for current user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. Use Command Prompt instead:
```cmd
python -m src.run_workflow --task "Question"
```

**Prevention:**
- Use Command Prompt or PowerShell with appropriate policy
- Sign scripts if required
- Document execution policy requirements
- Provide batch file alternatives

---

### Error: "Module not found after pip install"

**Symptom:**
```
ModuleNotFoundError: No module named 'openai'
```

**Cause:**
- Wrong Python environment active
- Virtual environment not activated
- Package installed in different Python

**Resolution:**

1. Verify active Python:
```bash
# Windows
where python
python --version

# macOS/Linux
which python
python --version
```

2. Activate virtual environment:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. Reinstall in correct environment:
```bash
pip install -r requirements.txt
```

4. Verify installation:
```bash
pip list | grep openai
```

**Prevention:**
- Always activate virtual environment before working
- Add activation to your shell profile
- Use virtual environment indicators in prompt
- Document environment setup in README

---

## Network Errors

### Error: "Connection refused"

**Symptom:**
```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Cause:**
- Service not running
- Wrong host/port
- Firewall blocking connection

**Resolution:**

1. Check if service is running:
```bash
# For local web API
curl http://localhost:5000/health
```

2. Verify host and port:
```bash
# In .env.local
WEBAPI_HOST=localhost
WEBAPI_PORT=5000
```

3. Check firewall:
```bash
# Windows
netsh advfirewall show currentprofile

# macOS/Linux
sudo iptables -L
```

**Prevention:**
- Start services before use
- Document required services
- Use health check endpoints
- Configure firewall rules

---

### Error: "DNS resolution failed"

**Symptom:**
```
DNSError: Failed to resolve 'api.openai.com'
```

**Cause:**
- DNS server issues
- Network connectivity problems
- Corporate proxy blocking

**Resolution:**

1. Test DNS:
```bash
# Windows
nslookup api.openai.com

# macOS/Linux
dig api.openai.com
```

2. Change DNS server:
```bash
# Windows: Network Settings → Adapter Properties → IPv4 → DNS
# Use Google DNS: 8.8.8.8, 8.8.4.4
# Or Cloudflare: 1.1.1.1, 1.0.0.1
```

3. Check proxy settings:
```bash
# In .env.local
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

**Prevention:**
- Use reliable DNS servers
- Configure proxy if required
- Test connectivity before workflows
- Monitor network status

---

## Quick Troubleshooting Checklist

When encountering an error:

1. **Check API Key**
   ```bash
   python -c "import os; print('Key set:', bool(os.getenv('OPENAI_API_KEY')))"
   ```

2. **Verify Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Test Network Connectivity**
   ```bash
   curl -I https://api.openai.com/v1/models
   ```

4. **Check Disk Space**
   ```bash
   # Windows: wmic logicaldisk get size,freespace,caption
   # macOS/Linux: df -h
   ```

5. **Validate Configuration**
   ```bash
   python scripts/validate_artifacts.py
   ```

6. **Review Logs**
   ```bash
   # Windows: type logs\workflow.log
   # macOS/Linux: tail -50 logs/workflow.log
   ```

7. **Try Dry-Run**
   ```bash
   python -m src.run_workflow --task "Test" --dry-run
   ```

8. **Check OpenAI Status**
   - Visit https://status.openai.com

## Getting Help

If errors persist after troubleshooting:

1. **Check Documentation**
   - [ONBOARDING.md](ONBOARDING.md) - Setup and configuration
   - [OPERATIONS.md](OPERATIONS.md) - Running workflows
   - [SECURITY.md](SECURITY.md) - Security and access control

2. **Search Issues**
   - GitHub Issues: https://github.com/yourusername/djp-workflow/issues
   - Search for similar errors

3. **Create New Issue**
   - Include error message (full traceback)
   - Describe steps to reproduce
   - Share relevant configuration (redact secrets!)
   - Include OS and Python version

4. **Community Support**
   - Discussions forum
   - Stack Overflow tag: `djp-workflow`

## Error Reporting Best Practices

When reporting errors:

```bash
# Capture full error output
python -m src.run_workflow --task "Test" 2>&1 | tee error.log

# Include system information
python --version
pip list
uname -a  # macOS/Linux
systeminfo  # Windows

# Share configuration (redacted)
# DO NOT share actual API keys!
cat .env.local | sed 's/sk-[^ ]*/sk-REDACTED/g'
```

## Related Documentation

- [ONBOARDING.md](ONBOARDING.md) - Getting started guide
- [TEMPLATES.md](TEMPLATES.md) - Template creation and troubleshooting
- [OPERATIONS.md](OPERATIONS.md) - Operational procedures
- [SECURITY.md](SECURITY.md) - Security best practices
