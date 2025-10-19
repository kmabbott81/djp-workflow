/**
 * Magic Box - Sprint 61a
 * Pure JavaScript SSE streaming client with cost tracking and safe action detection
 */

(function() {
    'use strict';

    // ============================================================================
    // Configuration
    // ============================================================================

    const CONFIG = {
        API_BASE: window.location.origin,
        ANON_LIMITS: {
            messagesPerHour: 20,
            totalMessages: 100,
            storageMB: 5,
            sessionDays: 7
        },
        PRICE_TABLE: {
            'gpt-4o': { input: 0.00250, output: 0.01000 },
            'gpt-4o-mini': { input: 0.00015, output: 0.00060 },
            'claude-3.5-sonnet': { input: 0.00300, output: 0.01500 }
        }
    };

    // ============================================================================
    // Anonymous Session Manager
    // ============================================================================

    class AnonymousSession {
        constructor() {
            this.sessionId = this.getOrCreateSessionId();
            this.usage = this.loadUsage();
        }

        getOrCreateSessionId() {
            const stored = localStorage.getItem('relay_anon_id');
            if (stored) {
                const { id, created } = JSON.parse(stored);
                const age = Date.now() - created;

                // Expire after 7 days
                if (age < CONFIG.ANON_LIMITS.sessionDays * 24 * 60 * 60 * 1000) {
                    return id;
                }
            }

            // Create new session
            const id = `anon_${crypto.randomUUID()}`;
            localStorage.setItem('relay_anon_id', JSON.stringify({
                id,
                created: Date.now()
            }));

            return id;
        }

        loadUsage() {
            const stored = localStorage.getItem('relay_anon_usage');
            if (stored) {
                return JSON.parse(stored);
            }

            return {
                messagesThisHour: [],
                totalMessages: 0,
                storageBytes: 0
            };
        }

        canSendMessage() {
            // Check hourly limit
            const now = Date.now();
            const oneHourAgo = now - 3600000;
            this.usage.messagesThisHour = this.usage.messagesThisHour.filter(
                timestamp => timestamp > oneHourAgo
            );

            if (this.usage.messagesThisHour.length >= CONFIG.ANON_LIMITS.messagesPerHour) {
                return {
                    allowed: false,
                    reason: 'hourly_limit',
                    resetIn: Math.min(...this.usage.messagesThisHour) + 3600000 - now
                };
            }

            // Check total limit
            if (this.usage.totalMessages >= CONFIG.ANON_LIMITS.totalMessages) {
                return {
                    allowed: false,
                    reason: 'total_limit',
                    upgrade: true
                };
            }

            return { allowed: true };
        }

        recordMessage() {
            this.usage.messagesThisHour.push(Date.now());
            this.usage.totalMessages++;
            this.saveUsage();
        }

        saveUsage() {
            localStorage.setItem('relay_anon_usage', JSON.stringify(this.usage));
        }

        getUsagePercent() {
            return (this.usage.totalMessages / CONFIG.ANON_LIMITS.totalMessages) * 100;
        }
    }

    // ============================================================================
    // Token Counter & Cost Tracker
    // ============================================================================

    class CostTracker {
        constructor(model = 'gpt-4o-mini') {
            this.model = model;
            this.pricing = CONFIG.PRICE_TABLE[model];
            this.inputTokens = 0;
            this.outputTokens = 0;
            this.totalCost = 0;
            this.sessionStart = Date.now();
            this.messageCount = 0;
        }

        approximateTokens(text) {
            // Rule of thumb: ~4 characters per token for English
            const baseCount = text.length / 4;
            let multiplier = 1;

            // Code detection (more tokens)
            if (/[{}\[\]()<>]/.test(text)) {
                multiplier *= 1.2;
            }

            // URL/Path detection (more tokens)
            if (/https?:\/\/|\/\w+\//.test(text)) {
                multiplier *= 1.3;
            }

            return Math.ceil(baseCount * multiplier);
        }

        addInput(text) {
            const tokens = this.approximateTokens(text);
            this.inputTokens += tokens;
            const cost = (tokens / 1000) * this.pricing.input;
            this.totalCost += cost;
            return { tokens, cost };
        }

        addOutput(text) {
            const tokens = this.approximateTokens(text);
            this.outputTokens += tokens;
            const cost = (tokens / 1000) * this.pricing.output;
            this.totalCost += cost;
            return { tokens, cost };
        }

        getCurrent() {
            return {
                inputTokens: this.inputTokens,
                outputTokens: this.outputTokens,
                totalTokens: this.inputTokens + this.outputTokens,
                totalCost: this.totalCost
            };
        }

        formatCost(cost) {
            if (cost < 0.0001) {
                return `$${(cost * 1000000).toFixed(0)}µ`; // microcents
            } else if (cost < 0.01) {
                return `$${(cost * 1000).toFixed(2)}m`; // millicents
            } else {
                return `$${cost.toFixed(6)}`;
            }
        }
    }

    // ============================================================================
    // Safe/Privileged Intent Detector
    // ============================================================================

    class IntentDetector {
        constructor() {
            this.safeKeywords = [
                'what', 'how', 'why', 'when', 'where', 'who',
                'explain', 'tell me', 'show me', 'find', 'search',
                'analyze', 'summarize', 'list', 'describe',
                'help', 'guide', 'teach', 'calculate', 'convert',
                'translate', 'format', 'check', 'verify', 'review'
            ];

            this.privilegedKeywords = [
                'send', 'email', 'message', 'post', 'publish',
                'create', 'delete', 'remove', 'update', 'modify',
                'execute', 'run', 'call', 'invoke', 'trigger',
                'share', 'invite', 'grant', 'revoke',
                'pay', 'transfer', 'purchase', 'subscribe',
                'deploy', 'commit', 'push', 'merge'
            ];
        }

        detectIntent(text) {
            const normalized = text.toLowerCase().trim();
            let privilegedCount = 0;
            let safeCount = 0;

            for (const keyword of this.privilegedKeywords) {
                if (normalized.includes(keyword)) {
                    privilegedCount++;
                }
            }

            for (const keyword of this.safeKeywords) {
                if (normalized.includes(keyword)) {
                    safeCount++;
                }
            }

            // If ANY privileged keyword found, require approval
            if (privilegedCount > 0) {
                return 'PRIVILEGED';
            }

            // If we have safe intents and no privileged, it's safe
            if (safeCount > 0) {
                return 'SAFE';
            }

            // Default to privileged (fail-safe)
            return 'PRIVILEGED';
        }
    }

    // ============================================================================
    // Message Queue (for early inputs)
    // ============================================================================

    class MessageQueue {
        constructor() {
            this.queue = [];
            this.isReady = false;
        }

        enqueue(message) {
            if (this.isReady) {
                return message; // Process immediately
            }
            this.queue.push(message);
            return null;
        }

        setReady() {
            this.isReady = true;
            return this.queue.splice(0); // Drain queue
        }
    }

    // ============================================================================
    // SSE Connection Manager
    // ============================================================================

    class ResilientSSEConnection {
        constructor(url, options = {}) {
            this.url = url;
            this.eventSource = null;
            this.retryCount = 0;
            this.maxRetryDelay = 5000;
            this.baseRetryDelay = 1000;
            this.reconnectTimer = null;
            this.isManuallyClosed = false;
            this.lastEventId = -1;
            this.messageHandler = options.onMessage || (() => {});
            this.errorHandler = options.onError || (() => {});
            this.openHandler = options.onOpen || (() => {});
        }

        connect() {
            if (this.isManulallyClosed) {
                return;
            }

            try {
                // Build URL with Last-Event-ID for recovery
                const connectUrl = this.lastEventId >= 0
                    ? `${this.url}?last_event_id=${this.lastEventId}`
                    : this.url;

                console.log(`[SSE] Connecting (attempt ${this.retryCount + 1})...`);

                this.eventSource = new EventSource(connectUrl);

                this.eventSource.onopen = () => {
                    console.log('[SSE] Connected');
                    this.retryCount = 0;
                    this.openHandler();
                };

                this.eventSource.onmessage = (event) => {
                    console.log(`[SSE] Message (id: ${event.lastEventId}): ${event.type}`);
                    // Update last event ID for recovery
                    this.lastEventId = parseInt(event.lastEventId || this.lastEventId, 10);
                    this.messageHandler({
                        type: 'message',
                        id: event.lastEventId,
                        data: event.data
                    });
                };

                this.eventSource.addEventListener('message_chunk', (event) => {
                    console.log(`[SSE] Chunk (id: ${event.lastEventId})`);
                    this.lastEventId = parseInt(event.lastEventId || this.lastEventId, 10);
                    try {
                        const data = JSON.parse(event.data);
                        this.messageHandler({
                            type: 'message_chunk',
                            id: event.lastEventId,
                            data: data
                        });
                    } catch (e) {
                        console.error('[SSE] Failed to parse chunk:', e);
                    }
                });

                this.eventSource.addEventListener('heartbeat', (event) => {
                    console.log(`[SSE] Heartbeat (id: ${event.lastEventId})`);
                    this.lastEventId = parseInt(event.lastEventId || this.lastEventId, 10);
                });

                this.eventSource.addEventListener('done', (event) => {
                    console.log(`[SSE] Done (id: ${event.lastEventId})`);
                    this.lastEventId = parseInt(event.lastEventId || this.lastEventId, 10);
                    try {
                        const data = JSON.parse(event.data);
                        this.messageHandler({
                            type: 'done',
                            id: event.lastEventId,
                            data: data
                        });
                    } catch (e) {
                        console.error('[SSE] Failed to parse done:', e);
                    }
                    this.close();
                });

                this.eventSource.addEventListener('error', (event) => {
                    console.error(`[SSE] Server error (id: ${event.lastEventId}):`, event);
                    this.lastEventId = parseInt(event.lastEventId || this.lastEventId, 10);
                    try {
                        const data = JSON.parse(event.data);
                        this.messageHandler({
                            type: 'error',
                            id: event.lastEventId,
                            data: data
                        });
                    } catch (e) {
                        console.error('[SSE] Failed to parse error:', e);
                    }
                    this.close();
                });

                this.eventSource.onerror = () => {
                    console.error('[SSE] Connection error');

                    if (this.eventSource.readyState === EventSource.CLOSED) {
                        console.log('[SSE] Connection closed by server');
                        this.eventSource.close();
                        this.reconnect();
                    } else if (this.eventSource.readyState === EventSource.CONNECTING) {
                        console.log('[SSE] Connecting...');
                    }
                };

            } catch (error) {
                console.error('[SSE] Error creating EventSource:', error);
                this.errorHandler(error);
                this.reconnect();
            }
        }

        reconnect() {
            if (this.isManulallyClosed) {
                return;
            }

            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
            }

            // Exponential backoff with jitter
            const baseDelay = this.baseRetryDelay * Math.pow(2, this.retryCount);
            const delay = Math.min(baseDelay, this.maxRetryDelay);
            const jitter = Math.random() * delay * 0.1; // 10% jitter
            const totalDelay = delay + jitter;

            console.log(`[SSE] Reconnecting in ${totalDelay.toFixed(0)}ms (retry ${this.retryCount + 1})`);

            this.retryCount++;
            this.reconnectTimer = setTimeout(() => this.connect(), totalDelay);
        }

        close() {
            console.log('[SSE] Closing connection');
            this.isManulallyClosed = true;
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
            }
        }
    }

    // ============================================================================
    // Message Deduplicator & Sequencer
    // ============================================================================

    class MessageSequencer {
        constructor() {
            this.processedIds = new Set();
            this.buffer = new Map();
            this.nextSequence = 0;
        }

        process(eventId, data) {
            const id = parseInt(eventId, 10);

            // Skip if already processed
            if (this.processedIds.has(id)) {
                console.log(`[Dedup] Skipping duplicate event ID ${id}`);
                return null;
            }

            // Mark as processed
            this.processedIds.add(id);

            // Handle out-of-order
            if (id < this.nextSequence) {
                console.log(`[Dedup] Late message (id: ${id}, expected >= ${this.nextSequence})`);
                return null;
            }

            if (id === this.nextSequence) {
                // Perfect sequence
                this.nextSequence++;
                this.flushBuffer();
                return data;
            }

            // Out of order - buffer it
            console.log(`[Dedup] Buffering out-of-order (id: ${id}, expected: ${this.nextSequence})`);
            this.buffer.set(id, data);
            return null;
        }

        flushBuffer() {
            let flushed = 0;
            while (this.buffer.has(this.nextSequence)) {
                const data = this.buffer.get(this.nextSequence);
                this.buffer.delete(this.nextSequence);
                this.nextSequence++;
                flushed++;
            }
            if (flushed > 0) {
                console.log(`[Dedup] Flushed ${flushed} buffered messages`);
            }
        }
    }

    // ============================================================================
    // Stall Detector
    // ============================================================================

    class StallDetector {
        constructor(timeoutMs = 30000) {
            this.timeoutMs = timeoutMs;
            this.lastEventTime = Date.now();
            this.stallTimer = null;
            this.onStall = () => {};
        }

        recordActivity() {
            this.lastEventTime = Date.now();
            if (this.stallTimer) {
                clearTimeout(this.stallTimer);
            }
            this.resetTimer();
        }

        resetTimer() {
            this.stallTimer = setTimeout(() => {
                console.warn(`[Stall] No events for ${this.timeoutMs}ms`);
                this.onStall();
            }, this.timeoutMs);
        }

        close() {
            if (this.stallTimer) {
                clearTimeout(this.stallTimer);
            }
        }
    }

    // ============================================================================
    // Magic Box Main Class
    // ============================================================================

    class MagicBox {
        constructor() {
            // State
            this.anonymousSession = new AnonymousSession();
            this.costTracker = new CostTracker();
            this.intentDetector = new IntentDetector();
            this.messageQueue = new MessageQueue();

            // SSE State
            this.sseConnection = null;
            this.messageSequencer = new MessageSequencer();
            this.stallDetector = new StallDetector(30000);
            this.currentStreamId = null;

            // DOM Elements
            this.elements = {
                messages: document.getElementById('messages'),
                userInput: document.getElementById('user-input'),
                sendButton: document.getElementById('send-button'),
                costPill: document.getElementById('cost-pill'),
                costValue: document.getElementById('cost-value'),
                latencyValue: document.getElementById('latency-value'),
                tokenCount: document.getElementById('token-count'),
                anonBadge: document.getElementById('anon-badge'),
                anonStatus: document.getElementById('anon-status'),
                usageFill: document.getElementById('usage-fill'),
                usageText: document.getElementById('usage-text')
            };

            // Timing
            this.lastRequestStart = 0;

            // Initialize
            this.init();
        }

        init() {
            // Bind events with passive listeners where possible
            this.elements.sendButton.addEventListener('click', () => this.sendMessage(), { passive: false });

            this.elements.userInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            }, { passive: false });

            // Auto-resize textarea with optimized handler
            let resizeTimeout;
            this.elements.userInput.addEventListener('input', () => {
                if (resizeTimeout) clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    this.elements.userInput.style.height = 'auto';
                    this.elements.userInput.style.height = this.elements.userInput.scrollHeight + 'px';
                }, 0);
            }, { passive: true });

            // Update UI
            this.updateAnonymousUI();

            // Report TTFV (critical path complete)
            this.reportTTFV();

            console.log('[Magic Box] Initialized');
        }

        reportTTFV() {
            if (window.performance && performance.measure) {
                try {
                    const navEntry = performance.getEntriesByType('navigation')[0];
                    if (navEntry) {
                        const ttfv = navEntry.domContentLoadedEventEnd - navEntry.fetchStart;
                        console.log(`[TTFV] ${ttfv.toFixed(0)}ms`);

                        // Defer metrics reporting to idle time to avoid blocking TTFV
                        if ('requestIdleCallback' in window) {
                            requestIdleCallback(() => this.sendMetrics(ttfv), { timeout: 5000 });
                        } else {
                            // Fallback: defer to next event loop
                            setTimeout(() => this.sendMetrics(ttfv), 100);
                        }
                    }
                } catch (e) {
                    // Performance API not available
                }
            }
        }

        sendMetrics(ttfv) {
            // Send to metrics endpoint without blocking user interaction
            fetch(`${CONFIG.API_BASE}/api/v1/metrics`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    metric: 'ttfv',
                    value: ttfv,
                    user_agent: navigator.userAgent
                }),
                keepalive: true  // Allow sending even if page unloads
            }).catch(() => {}); // Silent fail
        }

        updateAnonymousUI() {
            const usage = this.anonymousSession.usage;
            const percent = this.anonymousSession.getUsagePercent();

            this.elements.usageFill.style.width = `${percent}%`;
            this.elements.usageText.textContent = `${usage.totalMessages}/${CONFIG.ANON_LIMITS.totalMessages}`;

            // Show upgrade prompt at 80%
            if (percent >= 80) {
                this.elements.anonBadge.style.borderColor = '#ff9500';
                this.elements.anonStatus.textContent = 'Upgrade Soon';
            }
        }

        async sendMessage() {
            const text = this.elements.userInput.value.trim();
            if (!text) return;

            // Check limits
            const check = this.anonymousSession.canSendMessage();
            if (!check.allowed) {
                if (check.reason === 'hourly_limit') {
                    const minutes = Math.ceil(check.resetIn / 60000);
                    this.addSystemMessage(`Rate limit: Wait ${minutes} minutes or upgrade to continue`);
                } else if (check.reason === 'total_limit') {
                    this.addSystemMessage('You\'ve reached the anonymous message limit. Sign in to continue!');
                }
                return;
            }

            // Detect intent
            const intent = this.intentDetector.detectIntent(text);

            if (intent === 'PRIVILEGED') {
                // Show approval dialog
                const approved = confirm(
                    `This action may have side effects:\n"${text}"\n\nDo you want to proceed?`
                );
                if (!approved) {
                    this.addSystemMessage('Action cancelled');
                    return;
                }
            }

            // Clear input
            this.elements.userInput.value = '';
            this.elements.userInput.style.height = 'auto';

            // Disable send button
            this.elements.sendButton.disabled = true;

            // Add user message
            this.addMessage('user', text);

            // Record usage
            this.anonymousSession.recordMessage();
            this.updateAnonymousUI();

            // Track cost
            const { tokens } = this.costTracker.addInput(text);
            this.lastRequestStart = Date.now();

            // Start streaming
            this.streamResponse(text);
        }

        async streamResponse(prompt) {
            // Update pill to streaming state
            this.elements.costPill.classList.add('streaming');

            // Generate stream ID for recovery on disconnect
            this.currentStreamId = `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

            // Create assistant message placeholder
            const messageEl = this.addMessage('assistant', '');
            const contentEl = messageEl.querySelector('.message-content');

            let fullResponse = '';
            let chunkBuffer = '';
            let isStreaming = false;

            try {
                // Close previous connection if any
                if (this.sseConnection) {
                    this.sseConnection.close();
                }

                // Reset sequencer for new stream
                this.messageSequencer = new MessageSequencer();
                this.stallDetector.close();
                this.stallDetector = new StallDetector(30000);

                // Create SSE connection
                this.sseConnection = new ResilientSSEConnection('/api/v1/stream', {
                    onOpen: () => {
                        console.log('[Stream] Connected');
                        isStreaming = true;
                        this.stallDetector.recordActivity();
                    },
                    onMessage: (msg) => {
                        this.stallDetector.recordActivity();

                        // Deduplicate
                        const processedData = this.messageSequencer.process(msg.id, msg.data);
                        if (!processedData) {
                            return; // Duplicate or out of order
                        }

                        switch (msg.type) {
                            case 'message_chunk':
                                fullResponse += msg.data.content;
                                contentEl.textContent = fullResponse;
                                this.costTracker.addOutput(msg.data.content);

                                // Batch DOM updates: debounce cost pill and scroll updates
                                if (!chunkBuffer) {
                                    chunkBuffer = 'updating';
                                    requestAnimationFrame(() => {
                                        this.updateCostPill();
                                        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
                                        chunkBuffer = '';
                                    });
                                }
                                break;

                            case 'done':
                                console.log('[Stream] Complete:', msg.data);
                                // Update final costs immediately
                                this.updateCostPill();
                                requestAnimationFrame(() => {
                                    this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
                                });
                                break;

                            case 'error':
                                console.error('[Stream] Error:', msg.data);
                                contentEl.textContent = `Error: ${msg.data.error}`;
                                messageEl.classList.add('error');
                                break;

                            case 'heartbeat':
                                console.log('[Stream] Heartbeat');
                                break;
                        }
                    },
                    onError: (error) => {
                        console.error('[Stream] Error:', error);
                        if (!messageEl.classList.contains('error')) {
                            messageEl.classList.add('error');
                            contentEl.textContent = `Connection error: ${error.message}`;
                        }
                    }
                });

                // Setup stall handler
                this.stallDetector.onStall = () => {
                    console.warn('[Stream] Stalled, reconnecting...');
                    if (this.sseConnection) {
                        this.sseConnection.reconnect();
                    }
                };

                // Send request and start streaming
                const requestBody = {
                    user_id: this.anonymousSession.sessionId,
                    message: prompt,
                    model: 'gpt-4o-mini',
                    stream_id: this.currentStreamId
                };

                console.log('[Stream] Starting with request:', requestBody);

                // Make POST request to initiate stream
                // Note: SSE requires GET, but we need POST for request body
                // Solution: Use POST to endpoint that returns 200 + stream URL, then connect SSE
                // For now, we'll construct the request as query params
                const queryParams = new URLSearchParams({
                    user_id: requestBody.user_id,
                    message: requestBody.message,
                    model: requestBody.model,
                    stream_id: requestBody.stream_id
                });

                // Update SSE connection URL with query params
                this.sseConnection.url = `/api/v1/stream?${queryParams.toString()}`;
                this.sseConnection.connect();

            } catch (error) {
                console.error('[Stream] Exception:', error);
                contentEl.textContent = `Error: ${error.message}`;
                messageEl.classList.add('error');
            } finally {
                // Setup cleanup on stream end
                setTimeout(() => {
                    if (isStreaming) {
                        // Wait for actual completion
                        const checkComplete = setInterval(() => {
                            if (this.sseConnection && this.sseConnection.isManuallyClosed) {
                                clearInterval(checkComplete);
                                this.streamingComplete();
                            }
                        }, 100);
                    } else {
                        this.streamingComplete();
                    }
                }, 100);
            }
        }

        streamingComplete() {
            // Update pill to complete state
            this.elements.costPill.classList.remove('streaming');
            this.updateCostPill();

            // Re-enable send button
            this.elements.sendButton.disabled = false;

            // Focus input
            this.elements.userInput.focus();

            // Clean up
            this.stallDetector.close();
        }

        addMessage(role, content) {
            const messageEl = document.createElement('div');
            messageEl.className = `message ${role}`;

            const contentEl = document.createElement('div');
            contentEl.className = 'message-content';
            contentEl.textContent = content;

            messageEl.appendChild(contentEl);

            // Use requestAnimationFrame to batch DOM updates
            requestAnimationFrame(() => {
                this.elements.messages.appendChild(messageEl);
                // Schedule scroll for next frame to avoid layout thrashing
                requestAnimationFrame(() => {
                    this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
                });
            });

            return messageEl;
        }

        addSystemMessage(content) {
            const messageEl = this.addMessage('assistant', content);
            messageEl.classList.add('system');
            return messageEl;
        }

        updateCostPill() {
            const cost = this.costTracker.getCurrent();
            const latency = Date.now() - this.lastRequestStart;

            this.elements.costValue.textContent = this.costTracker.formatCost(cost.totalCost);
            this.elements.latencyValue.textContent = `${latency}ms`;
            this.elements.tokenCount.textContent = `(${cost.totalTokens} tokens)`;
        }
    }

    // ============================================================================
    // Initialize
    // ============================================================================

    // Wait for DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.magicBox = new MagicBox();
        });
    } else {
        window.magicBox = new MagicBox();
    }

})();
