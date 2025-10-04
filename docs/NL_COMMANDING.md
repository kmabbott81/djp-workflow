# Natural Language Commanding System

**Sprint 39** - Comprehensive Guide

## Overview

The Natural Language (NL) Commanding system transforms plain English commands into safe, auditable, cross-connector action plans. It provides a deterministic, offline parsing engine that requires **NO LLM calls** and **NO network connectivity** for command interpretation.

### Key Features

- **Pure Deterministic Parsing**: Regex-based intent extraction - no AI/LLM required
- **Cross-Connector Support**: Works with Teams, Slack, Outlook, Gmail, Notion
- **RBAC Enforcement**: Admin-level permissions required for actions
- **Approval Gating**: High-risk operations require human approval
- **Audit Trail**: Complete logging of all commands and executions
- **Offline Operation**: All parsing happens locally without network calls

### Architecture

```
Natural Language Command
         ↓
    Intent Parser (intents.py)
         ↓
    Entity Resolution (ner_contacts.py)
         ↓
    URG Grounding (search resources)
         ↓
    Action Planner (planner.py)
         ↓
    Risk Assessment
         ↓
    Approval Checkpoint (if high-risk)
         ↓
    Action Execution (executor.py)
         ↓
    Audit Logging
```

---

## Command Grammar

### Supported Verbs

| Verb | Description | Examples |
|------|-------------|----------|
| `email` | Send email via Outlook/Gmail | "Email the report to alice@example.com" |
| `message` | Send Teams/Slack message | "Message Alice about the project" |
| `forward` | Forward message/email | "Forward the contract to Legal team" |
| `reply` | Reply to message | "Reply to Bob's message with 'Sounds good'" |
| `schedule` | Create calendar event | "Schedule a meeting with Engineering team" |
| `create` | Create new resource | "Create a new page for project roadmap" |
| `update` | Update existing resource | "Update the status to Done" |
| `delete` | Delete resource | "Delete old messages from last month" |
| `find` | Search for resources | "Find messages from Alice about planning" |
| `list` | List resources | "List all contacts" |

### Target Patterns

**Email Addresses:**
```
"Email alice@example.com"
"Send to bob@company.com and charlie@company.com"
```

**Person Names:**
```
"Message Alice"
"Forward to Bob Smith"
"Send with Alice Johnson"
```

**Teams:**
```
"Message the Engineering team"
"Send to the Legal team"
```

**Channels:**
```
"Post in #general"
"Send to the Marketing channel"
```

### Artifact Patterns

**Quoted Strings:**
```
"Email 'Q4 Budget Report' to Alice"
"Reply with 'Sounds good, thanks!'"
```

**The [Thing] Pattern:**
```
"Forward the contract"
"Send the budget spreadsheet"
"Delete the old file"
```

**About [Topic] Pattern:**
```
"Find messages about planning"
"Search about project status"
```

### Constraint Patterns

**Source Connectors:**
```
"Find messages in Teams"
"Search Slack for files"
"Get Outlook emails"
"Find Gmail messages"
"Search Notion pages"
```

**Time Constraints:**
```
"from today"
"from yesterday"
"from this week"
"from last week"
"from this month"
"from last month"
```

**Labels/Tags:**
```
"with label urgent"
"with tag important"
```

**Folders:**
```
"in the Archive folder"
"in Budget Reports folder"
```

---

## Example Commands

### Email Operations

```bash
# Simple email
python scripts/nl.py run "Email alice@example.com about the meeting" --tenant acme

# Email with artifact
python scripts/nl.py run "Email the Q4 budget to alice@example.com" --tenant acme

# Email to multiple recipients
python scripts/nl.py run "Email the report to alice@example.com and bob@example.com" --tenant acme
```

### Messaging Operations

```bash
# Send Teams message
python scripts/nl.py run "Message Alice about the project" --tenant acme

# Send Slack message
python scripts/nl.py run "Message Bob in Slack" --tenant acme

# Message a team
python scripts/nl.py run "Message the Engineering team" --tenant acme
```

### Forward Operations

```bash
# Forward latest message
python scripts/nl.py run "Forward the contract to alice@example.com" --tenant acme

# Forward to team
python scripts/nl.py run "Forward the latest message to Legal team" --tenant acme

# Forward with source constraint
python scripts/nl.py run "Forward the latest Outlook email to Bob" --tenant acme
```

### Reply Operations

```bash
# Reply to message
python scripts/nl.py run "Reply to Bob's message with 'Sounds good'" --tenant acme

# Reply to latest from person
python scripts/nl.py run "Reply to Alice with 'Thanks for the update'" --tenant acme
```

### Search Operations

```bash
# Find messages
python scripts/nl.py run "Find messages from Alice" --tenant acme

# Find with constraints
python scripts/nl.py run "Find messages from Alice in Teams about planning" --tenant acme

# Find files
python scripts/nl.py run "Find files about Q4 budget" --tenant acme

# Find with time constraint
python scripts/nl.py run "Find messages from yesterday" --tenant acme
```

### Calendar Operations

```bash
# Schedule meeting
python scripts/nl.py run "Schedule a meeting with Alice and Bob" --tenant acme

# Schedule with details
python scripts/nl.py run "Schedule a meeting with Engineering team tomorrow" --tenant acme
```

### Create/Update/Delete Operations

```bash
# Create resource
python scripts/nl.py run "Create a new page for project roadmap" --tenant acme

# Update resource
python scripts/nl.py run "Update the project status" --tenant acme

# Delete (requires approval)
python scripts/nl.py dry "Delete old messages from last month" --tenant acme
```

---

## CLI Usage

### Commands

#### `dry` - Preview Command

Preview command execution without actually running it:

```bash
python scripts/nl.py dry "command" --tenant TENANT [--json]
```

**Options:**
- `--tenant` (required): Tenant ID
- `--user-id` (optional): User ID (default: "cli-user")
- `--json`: Output JSON format

**Example:**
```bash
python scripts/nl.py dry "Email alice@example.com" --tenant acme

# Output:
Command: Email alice@example.com
Action: email
Risk Level: low

Steps:
  1. Send email to Alice Smith (alice@example.com)
```

#### `run` - Execute Command

Execute command (with approval gating for high-risk):

```bash
python scripts/nl.py run "command" --tenant TENANT [--force] [--json]
```

**Options:**
- `--tenant` (required): Tenant ID
- `--user-id` (optional): User ID (default: "cli-user")
- `--force`: Skip approval (use with extreme caution)
- `--json`: Output JSON format

**Example:**
```bash
python scripts/nl.py run "Forward the contract to alice@example.com" --tenant acme

# If high-risk:
Status: PAUSED

PAUSED FOR APPROVAL

Checkpoint ID: nlp-approval-abc123

To resume after approval:
  python scripts/nl.py resume --checkpoint-id nlp-approval-abc123 --tenant acme
```

#### `resume` - Resume After Approval

Resume execution after approval checkpoint:

```bash
python scripts/nl.py resume --checkpoint-id ID --tenant TENANT [--json]
```

**Options:**
- `--checkpoint-id` (required): Checkpoint ID from paused execution
- `--tenant` (required): Tenant ID
- `--user-id` (optional): User ID (default: "cli-user")
- `--json`: Output JSON format

**Example:**
```bash
# After approving checkpoint via web UI or API
python scripts/nl.py resume --checkpoint-id nlp-approval-abc123 --tenant acme

# Output:
Status: SUCCESS

EXECUTION SUCCESSFUL

Completed 2 steps:
  1. Find message matching 'contract' - success
  2. Forward message to alice@example.com - success
```

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Command executed successfully |
| 1 | Error | Execution or parsing error |
| 2 | RBAC Denied | User lacks required permissions |
| 3 | Paused | Awaiting approval checkpoint |

---

## Security Model

### RBAC Requirements

**All NL command actions require Admin role.**

The action router enforces RBAC checks:
- User must have `Admin` role in the tenant
- Verified via `get_team_role(user_id, tenant)`
- Violations logged to audit trail

### High-Risk Operations

Operations automatically flagged as high-risk and requiring approval:

1. **Delete Operations**
   - Any `delete` action
   - Risk score: +50

2. **External Email**
   - Email to domains not in tenant's domain list
   - Risk score: +30

3. **Cross-Tenant Sharing**
   - Sharing outside tenant boundaries
   - Risk score: +30

4. **Bulk Operations**
   - More than 10 resources affected
   - Risk score: +20

### Risk Levels

| Risk Level | Score Range | Approval Required |
|------------|-------------|-------------------|
| Low | 0-19 | No |
| Medium | 20-49 | Optional (via config) |
| High | 50+ | Yes |

### Approval Workflow

1. High-risk plan detected → Create checkpoint
2. System pauses execution → Returns checkpoint ID
3. Operator reviews preview via dashboard/CLI
4. Operator approves/rejects via checkpoint API
5. Resume execution with checkpoint ID

**Approval Role:** Configurable via `NL_APPROVER_ROLE` (default: "Operator")

### Audit Trail

All NL command operations are logged:

**Audit Events:**
- Plan creation and risk assessment
- Approval checkpoint creation
- Approval/rejection decisions
- Step-by-step execution
- Success/failure outcomes
- RBAC denials

**Audit Fields:**
```json
{
  "tenant_id": "acme",
  "user_id": "user1",
  "action": "RUN_WORKFLOW",
  "resource_type": "nl_command",
  "resource_id": "nlp-abc123",
  "result": "SUCCESS",
  "timestamp": "2025-10-04T12:34:56Z",
  "metadata": {
    "checkpoint_id": "chk-456",
    "risk_level": "high",
    "step_count": 3
  }
}
```

---

## URG Grounding Process

### Contact Resolution

**Algorithm:**
1. Check if target is email address (contains "@")
2. If email: Search URG for contact with matching participant
3. If name: Search URG contacts, score by name match quality
4. Fallback: Check local alias fixtures (for testing)
5. Return Contact with email, user_id, source

**Name Match Scoring:**
- Exact title match: +100
- Title contains name: +50
- Title words match: +10 per word
- Snippet contains name: +5

### Resource Grounding

**Search Process:**
1. Build query from intent artifacts and targets
2. Apply type filter (message, file, event, etc.)
3. Apply source filter (teams, slack, outlook, gmail, notion)
4. Apply time constraints
5. Execute URG search with tenant isolation
6. Return top-scored results

**Query Construction:**
```python
# Example: "Forward the contract to Alice"
query = "contract"  # From artifact
type_filter = "message"  # Inferred from verb
source_filter = None  # No source constraint
limit = 1  # Only need one message to forward
```

---

## Action Planning

### Planning Algorithm

1. **Parse Intent**: Extract verb, targets, artifacts, constraints
2. **Validate Intent**: Ensure required components present
3. **Resolve Entities**: Ground targets to URG contacts
4. **Search Resources**: Find artifacts via URG search
5. **Select Connectors**: Determine source connectors
6. **Build Steps**: Create ordered ActionStep list
7. **Assess Risk**: Calculate risk score and approval requirement
8. **Generate Preview**: Create human-readable summary

### Action Selection

**Verb → Action Mapping:**

| Verb | Action(s) | Resource Type |
|------|-----------|---------------|
| email | contact.email | contact |
| message | contact.message | contact |
| forward | message.forward | message |
| reply | message.reply | message |
| schedule | event.create | event |
| create | page.create | page |
| update | {type}.update | (any) |
| delete | {type}.delete | (any) |
| find | search.execute | search |

### Multi-Connector Planning

Plans can span multiple connectors:

**Example: "Forward Teams message to Outlook email"**
```
Steps:
1. Search URG for Teams message (source: teams)
2. Resolve contact in Outlook directory (source: outlook)
3. Execute forward via Teams API → Outlook API
```

---

## Troubleshooting

### Parse Misses

**Symptom:** "Could not parse command"

**Causes:**
- Unrecognized verb
- Ambiguous command structure
- Missing required components

**Solutions:**
1. Use supported verb from grammar
2. Add explicit targets: "Email **alice@example.com**"
3. Use quoted strings for artifacts: "Forward **'the contract'**"
4. Check command against examples

### Contact Resolution Failures

**Symptom:** "Could not resolve any contacts"

**Causes:**
- Name not in URG index
- Typo in name/email
- Contact not in tenant scope

**Solutions:**
1. Use full email address instead of name
2. Verify contact exists in tenant
3. Check URG index status
4. Use `find` to search for contact first

### Stuck Approval Checkpoints

**Symptom:** Command paused but no approval UI

**Causes:**
- Checkpoint not visible in dashboard
- Approval role misconfigured
- Checkpoint expired (default: 72h)

**Solutions:**
1. Check checkpoint status:
   ```python
   from src.orchestrator.checkpoints import get_checkpoint
   get_checkpoint("chk-123")
   ```

2. Approve via API:
   ```python
   from src.orchestrator.checkpoints import approve_checkpoint
   approve_checkpoint("chk-123", approved_by="operator1")
   ```

3. Check `NL_APPROVER_ROLE` environment variable

### Action Execution Errors

**Symptom:** "Action failed" or step errors

**Causes:**
- RBAC denial (not Admin)
- Connector authentication failure
- Resource not accessible
- Invalid payload

**Solutions:**
1. Verify user has Admin role
2. Check connector credentials
3. Verify resource exists and is accessible
4. Review audit log for detailed error
5. Use `dry` mode to preview plan

---

## Environment Variables

```bash
# Approval Configuration
NL_APPROVER_ROLE=Operator  # Role required to approve high-risk commands

# Risk Configuration
NL_HIGH_RISK_ACTIONS=delete,external_email,share_outside  # Comma-separated
NL_APPROVE_MEDIUM=false  # Require approval for medium-risk (default: false)

# Search Configuration
NL_MAX_MATCHES=10  # Maximum resources to act on

# Audit Configuration
AUDIT_DIR=audit  # Audit log directory

# Checkpoint Configuration
CHECKPOINTS_PATH=logs/checkpoints.jsonl  # Checkpoint store path
APPROVAL_EXPIRES_H=72  # Approval expiration hours
```

---

## API Usage

### Python API

```python
from src.nl import make_plan, execute_plan

# Create plan
plan = make_plan(
    command="Email the report to alice@example.com",
    tenant="acme",
    user_id="user1"
)

# Preview
print(plan.preview)
print(f"Risk: {plan.risk_level}")
print(f"Steps: {len(plan.steps)}")

# Dry run
result = execute_plan(
    plan,
    tenant="acme",
    user_id="user1",
    dry_run=True
)

# Execute
result = execute_plan(
    plan,
    tenant="acme",
    user_id="user1",
    dry_run=False
)

if result.status == "paused":
    print(f"Awaiting approval: {result.checkpoint_id}")
elif result.status == "success":
    print("Executed successfully")
    print(f"Audit IDs: {result.audit_ids}")
elif result.status == "error":
    print(f"Error: {result.error}")
```

### Resume After Approval

```python
from src.nl import resume_plan

result = resume_plan(
    checkpoint_id="nlp-approval-abc123",
    tenant="acme",
    user_id="user1"
)

print(f"Status: {result.status}")
for step_result in result.results:
    print(f"  {step_result['description']}: {step_result['status']}")
```

---

## Testing

### Unit Tests

Run all NL command tests:

```bash
# All NL tests
pytest tests/test_nl_*.py -v

# Intent parsing
pytest tests/test_nl_intents.py -v

# Action planning
pytest tests/test_nl_planner.py -v

# Execution
pytest tests/test_nl_executor.py -v

# CLI
pytest tests/test_nl_cli.py -v
```

### Integration Tests

Test end-to-end flow:

```python
def test_email_flow():
    """Test complete email command flow."""
    # Parse intent
    intent = parse_intent("Email alice@example.com")
    assert intent.verb == "email"

    # Make plan
    plan = make_plan(intent.original_command, "test-tenant", "user1")
    assert len(plan.steps) > 0

    # Execute (dry run)
    result = execute_plan(plan, tenant="test-tenant", user_id="user1", dry_run=True)
    assert result.status == "dry"
```

### Test Fixtures

Common test fixtures for URG resources:

```python
# Mock contact
contact = Contact(
    name="Alice Smith",
    email="alice@example.com",
    user_id="alice_id",
    source="outlook",
    graph_id="contact-alice-123"
)

# Mock message
message = {
    "id": "msg-123",
    "type": "message",
    "title": "Meeting notes",
    "source": "teams",
    "participants": ["alice@example.com"],
    "timestamp": "2025-10-04T10:00:00Z"
}
```

---

## Performance

### Parsing Performance

- Intent parsing: < 1ms (deterministic regex)
- Contact resolution: < 10ms (URG search)
- Plan generation: < 50ms (URG grounding + planning)

**No LLM latency** - all processing is local and deterministic.

### Scalability

- URG search: O(log n) with indexed fields
- Action execution: Sequential (by design for safety)
- Bulk operations: Limited to `NL_MAX_MATCHES` (default: 10)

---

## Future Enhancements

Planned for future sprints:

1. **Conditional Actions**: "If X then Y" logic
2. **Scheduled Commands**: "Email report every Monday"
3. **Template Commands**: Saved command shortcuts
4. **Multi-step Transactions**: Rollback on failure
5. **Enhanced NER**: Better name/entity recognition
6. **Voice Input**: Speech-to-text integration

---

## Support

For issues or questions:

1. Check this documentation
2. Review troubleshooting section
3. Check audit logs for execution details
4. Review test files for usage examples
5. Contact operations team

---

**Version:** Sprint 39
**Last Updated:** 2025-10-04
**Status:** Production Ready
