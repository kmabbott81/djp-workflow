# Sprint 56: Chat-Like UI + Streaming Responses

**Status:** 🟢 READY TO START
**Duration:** 3 weeks (Weeks 1-3)
**Phase:** Product Excellence - UX Polish
**Depends on:** Sprint 55 Week 3 (UI Unblocked) ✅

---

## North Star Alignment

This sprint directly advances toward:
- ✅ **ChatGPT-level polish** - Conversational UI with streaming responses
- ✅ **Multi-AI orchestration** - Foundation for selecting AI provider
- ✅ **Single dashboard** - Unified experience better than competitors

**Strategic Goal:** Transform the current form-based UI into a ChatGPT-like conversational interface that streams AI planning in real-time, creating a "wow" moment for users.

---

## Sprint Goals

### Week 1: Chat UI Foundation
**Objective:** Replace form-based UI with conversational chat interface

**Model Constraint:** OpenAI ONLY during Weeks 1-2. Multi-model routing deferred to Week 3 to avoid premature branching.

**Deliverables:**
1. Chat message UI components (user messages, AI responses)
2. Message history persistence (localStorage for now, DB later)
3. Conversational prompt handling (multi-turn context)
4. Message timestamps and metadata display
5. **Stub conversation/message persistence API (no frontend use yet)**
6. **XSS sanitization setup with DOMPurify (safe defaults from day 1)**

**Success Criteria:**
- User can type messages in a chat interface
- AI responses appear as chat bubbles
- Previous messages remain visible in scrollable history
- UI feels responsive and polished (animations, transitions)

**Definition of Done:**
> Week 1 is done when a user can send multi-turn messages and see persistent history without refresh, with no layout or scrolling jank. All HTML output is sanitized through DOMPurify.

### Week 2: Streaming Responses
**Objective:** Implement real-time streaming of AI planning responses

**Model Constraint:** OpenAI ONLY. Multi-model routing deferred to Week 3.

**Deliverables:**
1. Server-Sent Events (SSE) endpoint for streaming (OpenAI only)
2. **Polling fallback endpoint (stub implementation for proxy/firewall issues)**
3. Frontend SSE client with progressive rendering
4. Streaming token-by-token display (typewriter effect)
5. Error handling and reconnection logic with exponential backoff
6. **Latency and error telemetry (browser perf timers + Prometheus counters)**

**Success Criteria:**
- User sees AI response appear word-by-word in real-time
- No jarring UI updates or flickering
- Graceful handling of connection drops (auto-reconnect or fallback to polling)
- Performance remains smooth with long responses
- First token latency < 500ms (measured and logged)

**Definition of Done:**
> Week 2 is done when streaming works smoothly for 10+ consecutive messages, with automatic fallback if SSE fails, and telemetry data confirms < 500ms first token latency and 60 FPS rendering.

### Week 3: Enhanced Features + Polish
**Objective:** Add power-user features and visual polish

**Deliverables:**
1. Code block syntax highlighting in responses
2. Markdown rendering for rich formatting (already sanitized via DOMPurify)
3. Copy-to-clipboard buttons for code snippets
4. Stop/regenerate buttons for active generations
5. Model selector dropdown (GPT-4, Claude, Gemini) - NOW enabled
6. Dark mode toggle
7. **Scroll anchoring (auto-scroll with pause on manual scroll)**
8. **Conversation sidebar (stretch goal - titles, timestamps, clickable)**

**Success Criteria:**
- UI looks professional and polished (ChatGPT quality)
- Code blocks are syntax-highlighted and copyable
- User can stop generation mid-stream
- Model switching works end-to-end (OpenAI, Anthropic, Google)
- Dark mode is visually appealing
- Scrolling feels smooth and natural (no jank on long responses)

**Definition of Done:**
> Week 3 is done when the UI matches ChatGPT polish level, multi-model switching works (OpenAI + Claude + Gemini), dark mode is production-ready, and scroll behavior feels professional with no jank on 10k+ token responses.

---

## Technical Architecture

### Frontend Components

```
static/app/
├── index.html (refactored for chat UI)
├── js/
│   ├── chat.js (message handling, history)
│   ├── streaming.js (SSE client, progressive rendering)
│   ├── markdown.js (marked.js + syntax highlighting)
│   └── models.js (AI provider selection logic)
└── css/
    ├── chat.css (chat bubble styles, animations)
    └── themes.css (light/dark mode)
```

### Backend Endpoints

```python
# src/webapi_ai_endpoints.py

@app.post("/ai/chat")
async def chat_stream(
    request: Request,
    message: str,
    conversation_id: Optional[str] = None,
    model: str = "gpt-4"
) -> StreamingResponse:
    """
    Stream AI planning response in real-time.

    Returns Server-Sent Events (SSE) with progressive tokens.
    """
    pass

@app.get("/ai/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict:
    """Retrieve full conversation history."""
    pass
```

### Data Model

```python
# Conversation storage (PostgreSQL)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(50) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    model VARCHAR(100), -- 'gpt-4', 'claude-sonnet-4', etc.
    metadata JSONB, -- tokens, latency, etc.
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Implementation Plan

### Week 1: Chat UI Foundation

#### Task 1.1: Design Chat UI Layout
**File:** `static/app/index.html`
**Changes:**
- Replace form with chat container
- Add message list area (scrollable)
- Add input box at bottom (fixed position)
- Add send button with keyboard shortcut (Enter to send)

**UI Structure:**
```html
<div id="chat-container">
  <div id="messages-area">
    <!-- Message bubbles appear here -->
  </div>
  <div id="input-area">
    <textarea id="user-input" placeholder="Type a message..."></textarea>
    <button id="send-btn">Send</button>
  </div>
</div>
```

#### Task 1.2: Message Bubble Components
**File:** `static/app/js/chat.js`
**Features:**
- User message bubble (right-aligned, blue)
- AI message bubble (left-aligned, gray)
- Timestamp display
- Avatar icons (user icon, AI logo)

**API:**
```javascript
function addUserMessage(text) {
  // Append user message bubble to messages-area
}

function addAIMessage(text, streaming = false) {
  // Append AI message bubble
  // If streaming=true, return messageElement for progressive updates
}
```

#### Task 1.3: Message History Persistence
**File:** `static/app/js/chat.js`
**Features:**
- Save messages to localStorage on send/receive
- Load messages from localStorage on page load
- Clear history button

**API:**
```javascript
function saveConversation(messages) {
  localStorage.setItem('conversation', JSON.stringify(messages));
}

function loadConversation() {
  return JSON.parse(localStorage.getItem('conversation') || '[]');
}
```

#### Task 1.4: Basic CSS Styling
**File:** `static/app/css/chat.css`
**Features:**
- Chat bubble styles (rounded corners, shadows, padding)
- Message area scrolling (smooth, auto-scroll to bottom)
- Input area fixed at bottom
- Responsive layout (mobile-friendly)

---

### Week 2: Streaming Responses

#### Task 2.1: SSE Endpoint Implementation
**File:** `src/webapi_ai_endpoints.py`
**Implementation:**
```python
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/ai/chat/stream")
@require_scopes(["actions:preview"])
async def chat_stream(request: Request, message: str, model: str = "gpt-4"):
    """Stream AI planning response using Server-Sent Events."""

    async def event_generator():
        # Call OpenAI/Claude/Gemini with streaming enabled
        async for chunk in ai_client.chat_stream(message, model=model):
            yield f"data: {json.dumps({'token': chunk})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

#### Task 2.2: Frontend SSE Client
**File:** `static/app/js/streaming.js`
**Implementation:**
```javascript
function streamAIResponse(message, onToken, onComplete, onError) {
  const eventSource = new EventSource(
    `/ai/chat/stream?message=${encodeURIComponent(message)}`
  );

  eventSource.onmessage = (event) => {
    if (event.data === '[DONE]') {
      eventSource.close();
      onComplete();
      return;
    }

    const data = JSON.parse(event.data);
    onToken(data.token);
  };

  eventSource.onerror = (error) => {
    eventSource.close();
    onError(error);
  };

  return eventSource; // Allow caller to stop stream
}
```

#### Task 2.3: Progressive Rendering
**File:** `static/app/js/chat.js`
**Integration:**
```javascript
function sendMessage(text) {
  addUserMessage(text);

  const aiMessageElement = addAIMessage('', streaming = true);
  let fullResponse = '';

  const stream = streamAIResponse(
    text,
    // onToken
    (token) => {
      fullResponse += token;
      aiMessageElement.textContent = fullResponse;
    },
    // onComplete
    () => {
      console.log('Stream complete');
      saveConversation([...messages, {role: 'assistant', content: fullResponse}]);
    },
    // onError
    (error) => {
      console.error('Stream error:', error);
      aiMessageElement.textContent += '\n\n[Error: Connection lost]';
    }
  );
}
```

#### Task 2.4: Stop/Regenerate Buttons
**File:** `static/app/js/chat.js`
**Features:**
- Stop button appears during streaming
- Regenerate button appears after completion
- Stop closes EventSource
- Regenerate resends last user message

---

### Week 3: Enhanced Features + Polish

#### Task 3.1: Markdown Rendering
**Library:** [marked.js](https://marked.js.org/) + [highlight.js](https://highlightjs.org/)
**File:** `static/app/js/markdown.js`
**Implementation:**
```javascript
import marked from 'marked';
import hljs from 'highlight.js';

marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  }
});

function renderMarkdown(text) {
  return marked.parse(text);
}
```

#### Task 3.2: Code Block Enhancements
**File:** `static/app/css/chat.css`
**Features:**
- Copy button in top-right of code blocks
- Language label display
- Line numbers (optional)

**JS:**
```javascript
function addCopyButton(codeBlock) {
  const btn = document.createElement('button');
  btn.textContent = 'Copy';
  btn.className = 'copy-btn';
  btn.onclick = () => {
    navigator.clipboard.writeText(codeBlock.textContent);
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  };
  codeBlock.parentElement.appendChild(btn);
}
```

#### Task 3.3: Model Selector Dropdown
**File:** `static/app/index.html`
**UI:**
```html
<div id="model-selector">
  <select id="model-dropdown">
    <option value="gpt-4">GPT-4 (OpenAI)</option>
    <option value="claude-sonnet-4">Claude Sonnet 4 (Anthropic)</option>
    <option value="gemini-pro">Gemini Pro (Google)</option>
  </select>
</div>
```

**Backend:**
Modify `/ai/chat/stream` to route to appropriate AI provider based on `model` parameter.

#### Task 3.4: Dark Mode Toggle
**File:** `static/app/css/themes.css`
**Implementation:**
```css
:root {
  --bg-color: #ffffff;
  --text-color: #000000;
  --user-bubble: #007bff;
  --ai-bubble: #f1f1f1;
}

[data-theme="dark"] {
  --bg-color: #1e1e1e;
  --text-color: #ffffff;
  --user-bubble: #0056b3;
  --ai-bubble: #2d2d2d;
}
```

**JS:**
```javascript
function toggleDarkMode() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
}
```

---

## Testing Strategy

### Unit Tests
- Test message rendering functions
- Test localStorage save/load
- Test markdown parsing with code blocks
- Test SSE client reconnection logic

### Integration Tests
- Test full chat flow (user → streaming → display)
- Test model switching
- Test conversation persistence across page reloads
- Test error handling (network failures, malformed SSE)

### Manual Testing
- Test on multiple browsers (Chrome, Firefox, Safari, Edge)
- Test on mobile devices (responsive layout)
- Test with long responses (performance, scrolling)
- Test with code-heavy responses (syntax highlighting)
- Test dark mode readability

---

## Success Metrics

### Qualitative
- ✅ UI feels as polished as ChatGPT
- ✅ Streaming is smooth and responsive
- ✅ Code blocks are readable and copyable
- ✅ Dark mode looks professional
- ✅ Mobile experience is usable

### Quantitative
- ⚡ First token latency < 500ms
- ⚡ Streaming updates 60 FPS (no dropped frames)
- ⚡ Page load < 2 seconds
- ⚡ Message history loads < 100ms

### User Experience
- 🎯 User says "wow" when they see streaming
- 🎯 User finds code blocks easy to copy
- 🎯 User prefers this over the old form UI
- 🎯 User can switch models without confusion

---

## Risk Mitigation

### Risk 1: Streaming Performance Degrades with Long Responses
**Mitigation:**
- Use virtual scrolling for message list
- Throttle DOM updates to 60 FPS max
- Profile with Chrome DevTools to identify bottlenecks

### Risk 2: SSE Connection Drops Frequently
**Mitigation:**
- Implement automatic reconnection with exponential backoff
- Show connection status indicator to user
- Fall back to polling if SSE fails repeatedly

### Risk 3: Markdown Rendering Introduces XSS Vulnerabilities
**Mitigation:**
- Use DOMPurify library to sanitize HTML output
- Configure marked.js to escape HTML by default
- Test with malicious input (script tags, event handlers)

### Risk 4: Multi-Model Support is Complex
**Mitigation:**
- Start with OpenAI only in Week 1-2
- Add Claude/Gemini in Week 3 as stretch goal
- Abstract AI provider logic into separate module

---

## Dependencies

### External Libraries
- **marked.js** - Markdown parsing (MIT license, 50KB)
- **highlight.js** - Syntax highlighting (BSD license, 100KB)
- **DOMPurify** - XSS sanitization (Apache 2.0, 20KB)

### Backend Services
- OpenAI API (already configured)
- Anthropic API (need API key for Claude)
- Google AI API (need API key for Gemini)

### Infrastructure
- PostgreSQL for conversation storage (already set up)
- Redis for session management (already set up)

---

## Future Enhancements (Post-Sprint 56)

### Sprint 57: Advanced Workflow Features
- Visual workflow builder (drag-and-drop)
- Workflow templates library
- Conditional logic (if/else branches)
- Loop constructs (iterate over lists)

### Sprint 58: Collaboration Features
- Multi-user workspaces
- Shared conversation history
- Real-time co-editing
- Comment threads on messages

### Sprint 59: Production Deployment
- Railway hosting configuration
- Monitoring and alerting
- Rate limiting and quotas
- Usage analytics dashboard

---

## Conclusion

Sprint 56 transforms the UI from "functional" to "delightful". By implementing ChatGPT-level streaming and polish, we create a user experience that rivals or exceeds the best AI interfaces on the market.

This sprint is the foundation for multi-AI orchestration and advanced workflow features in future sprints. Every subsequent feature will build on this polished, conversational UI paradigm.

**Let's ship something users will love.** 🚀

---

**Sprint 56 Status:** 🟢 READY TO START
**Estimated Duration:** 3 weeks
**Key Milestone:** ChatGPT-level UI Polish
