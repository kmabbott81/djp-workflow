---
version: 1.4.0
updated: 2025-10-18T16:45:00Z
current_sprint: 61a
status: ACTIVE
sha256: pending_calculation
---

# Relay AI Orchestrator — Product Roadmap v1.4.0

## 🎯 North Star

**"An invisible butler that's everywhere, with zero friction, visible trust, and real work done."**

Make Relay feel more powerful than ChatGPT, more transparent than Claude, more connected than Perplexity — for less than $20/mo.

---

## 📍 Current State (October 18, 2025)

### Sprint 61a: Magic Box [IN PROGRESS]
- **Goal**: Ship `/magic` page in 72 hours
- **Exit Criteria**:
  - [ ] Pure HTML/JS (no framework)
  - [ ] SSE streaming with auto-reconnect
  - [ ] Cost + latency pill always visible
  - [ ] Safe actions auto-execute
  - [ ] Anonymous sessions work
  - [ ] TTFV < 1.5s on staging
- **Deadline**: October 21, 2025
- **Owner**: Claude Code (Opus model for architecture)

### Completed
- ✅ **v1.0.0**: Backend infrastructure (Oct 18)
  - Zero-downtime schema migration
  - Workspace isolation
  - Telemetry pipeline
  - 59/59 tests passing

---

## 🏗️ Architecture Decisions [LOCKED]

| Component | Decision | Rationale |
|-----------|----------|-----------|
| **Auth** | Supabase | Magic links + OAuth + BYO key encryption |
| **Database** | Postgres + pgvector | Threads, memory, embeddings |
| **Files** | S3/R2 + tus | Resumable uploads, CDN-friendly |
| **Embedding Model** | `text-embedding-3-small` | Cost-effective, good quality |
| **Chunk Size** | 512 tokens, 64 overlap | Balance context/cost |
| **Frontend (Magic)** | Vanilla JS | Speed, no build step |
| **Frontend (Cockpit)** | Next.js + shadcn/ui | Full app later |
| **Extension** | Chrome MV3 | Cmd+K launcher only |
| **Memory** | Summaries + entities | Not graph viz yet |
| **Stream** | SSE | Works, WebSocket later if needed |
| **Local Sync** | File System Access API | Chrome-only, R4 |

---

## 📦 Release Plan

### R0.5: Magic Box ⚡ [Sprint 61a+b]
**Target**: October 21-28, 2025
- `/magic` page with streaming
- Anonymous sessions
- Safe vs privileged detection
- Cost/latency transparency
- Cmd+K extension (61b)

### R1: Memory & Context 🧠 [Sprint 63]
**Target**: November 4-11, 2025
- Thread summarization (every 20 msgs)
- Entity extraction (people, projects, dates)
- Simple recall: "As we discussed..."
- Opt-out controls

### R2: Files & Knowledge 📚 [Sprint 64]
**Target**: November 11-18, 2025
- Upload to S3 (5-10GB/user)
- Chunk + embed with pgvector
- Citation in responses
- Attach files to prompts

### R3: Connectors 🔌 [Sprint 65]
**Target**: November 18-25, 2025
- Google Drive + Gmail (OAuth)
- Notion read-only
- Local folder sync (File System API)
- Unified search

### R4: Cockpit 🎛️ [Sprint 66]
**Target**: December 2025
- Next.js full app
- Threads management
- Jobs dashboard
- Cost analytics
- Team sharing

---

## 🔧 Technical Specifications

### Safe vs Privileged Actions
```javascript
const SAFE_ACTIONS = {
  search: ['web', 'files', 'memory'],
  read: ['public_urls', 'uploaded_docs'],
  analyze: ['text', 'code', 'data'],
  plan: ['*']
};

const PRIVILEGED_ACTIONS = {
  write: ['email', 'slack', 'github'],
  modify: ['calendar', 'files', 'database'],
  execute: ['code', 'api_calls', 'webhooks']
};
```

### Anonymous Limits
```javascript
const ANON_LIMITS = {
  messagesPerHour: 20,
  totalMessages: 100,
  storageMB: 5,
  sessionDays: 7
};
```

### Cost Table
```javascript
const PRICE_TABLE = {
  'gpt-4o': { input: 0.00250, output: 0.01000 },
  'gpt-4o-mini': { input: 0.00015, output: 0.00060 },
  'claude-3.5-sonnet': { input: 0.00300, output: 0.01500 },
  'text-embedding-3-small': { input: 0.00002, output: 0 }
};
```

### Database Schema
```sql
-- Core tables (Sprint 61b)
users(id, email, created_at)
projects(id, owner_user_id, name, created_at)
threads(id, project_id, title, created_at, updated_at)
messages(id, thread_id, role, content, tokens_in, tokens_out,
         cost_usd, latency_ms, created_at)

-- Memory tables (Sprint 63)
memory_nodes(id, user_id, kind, title, embedding vector(1536),
             data jsonb, created_at)
memory_edges(src_id, dst_id, relation, weight, created_at)

-- Files & connectors (Sprint 64-65)
files(id, user_id, storage, uri, title, mime, size_bytes,
      embedding vector(1536), created_at)
api_keys(id, user_id, provider, enc_key, created_at)
```

---

## 📊 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| TTFV (Time to First Value) | < 1.5s | TBD |
| SSE Stream Completion | > 99.9% | TBD |
| Cost Transparency | 100% of responses | TBD |
| Memory Recall@5 | > 90% | TBD |
| Anonymous → Registered | > 20% | TBD |
| Daily Active Extension Users | > 50% of registered | TBD |

---

## 🚦 Feature Flags

```python
FEATURE_FLAGS = {
    'ENABLE_MAGIC_BOX': True,  # Sprint 61a
    'MAGIC_BOX_ROLLOUT_PCT': 100,  # Full rollout for now
    'ENABLE_MEMORY': False,  # Sprint 63
    'ENABLE_FILES': False,  # Sprint 64
    'ENABLE_CONNECTORS': False,  # Sprint 65
    'ENABLE_EXTENSION': False,  # Sprint 61b
}
```

---

## 📝 Sprint 61a Checklist

- [ ] Create `/magic` route in FastAPI
- [ ] Add `static/magic/index.html`
- [ ] Add `static/magic/magic.js` with SSE client
- [ ] Add `static/magic/magic.css` with minimal styles
- [ ] Implement safe/privileged action detection
- [ ] Add cost/latency pill updates
- [ ] Add anonymous session management
- [ ] Add SSE auto-reconnect with dedupe
- [ ] Test TTFV < 1.5s
- [ ] Test network resilience
- [ ] Deploy with feature flag
- [ ] Document in README

---

## 🔗 Key Resources

- **Backend API**: https://relay-production-f2a6.up.railway.app
- **Current UI (temp)**: https://relay-production-f2a6.up.railway.app/static/app/chat.html
- **GitHub**: https://github.com/kmabbott81/djp-workflow
- **Telemetry**: Grafana dashboard (internal)
- **Slack**: #relay-dev (internal)

---

## 📜 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.4.0 | 2025-10-18 | Added Sprint 61a specs, locked architecture decisions |
| 1.3.0 | 2025-10-18 | Opus feedback integrated, simplified extension |
| 1.2.0 | 2025-10-18 | Sonnet review, memory architecture detailed |
| 1.1.0 | 2025-10-18 | ChatGPT synthesis, dual-track strategy |
| 1.0.0 | 2025-10-18 | Initial roadmap, 7-release plan |

---

## 🤝 How to Use This Roadmap

### For Claude Code
1. Always check `ROADMAP.md` version at conversation start
2. Current sprint is **61a** (Magic Box)
3. Use Opus model for architecture, Sonnet for implementation
4. Reference architecture decisions as locked constraints

### For ChatGPT
1. Reference this document via memory feature
2. Check version number for updates
3. Current focus: Sprint 61a implementation
4. Respect locked architecture decisions

### For New Contributors
1. Read this entire document first
2. Check current sprint status
3. Follow the technical specifications exactly
4. Don't change locked decisions without RFC

---

## ⚠️ Do Not Change Without Approval

- Authentication provider (Supabase)
- Embedding model (text-embedding-3-small)
- Sprint 61a scope (Magic Box only)
- Safe/privileged action definitions
- Anonymous session limits

---

**Last Updated**: October 18, 2025, 4:45 PM
**Next Review**: October 21, 2025 (Sprint 61a completion)
