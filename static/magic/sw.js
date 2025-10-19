/**
 * Magic Box Service Worker
 * Caching strategy for offline support and repeat visits
 * - Static assets: Cache-first (CSS, JS, fonts)
 * - HTML: Stale-while-revalidate (keep fresh index)
 * - API: Network-first (prioritize fresh data)
 */

const CACHE_VERSION = 'magic-v1.0.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

const STATIC_ASSETS = [
    '/static/magic/index.html',
    '/static/magic/magic.js',
    '/static/magic/sw.js'
];

/**
 * Install: Pre-cache critical assets
 */
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
            .catch(err => console.error('[SW] Install error:', err))
    );
});

/**
 * Activate: Clean up old cache versions
 */
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(name => {
                    if (name !== STATIC_CACHE && name !== RUNTIME_CACHE) {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

/**
 * Fetch: Implement caching strategies
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests and external origins
    if (request.method !== 'GET' || url.origin !== location.origin) {
        return;
    }

    // Strategy 1: HTML (Stale-While-Revalidate)
    if (request.destination === 'document' || url.pathname === '/magic' || url.pathname.endsWith('.html')) {
        event.respondWith(
            caches.match(request)
                .then(cached => {
                    const fetchPromise = fetch(request).then(response => {
                        // Cache successful responses
                        if (response.ok) {
                            const clone = response.clone();
                            caches.open(STATIC_CACHE).then(cache => {
                                cache.put(request, clone);
                            });
                        }
                        return response;
                    });

                    // Return cached version immediately, or wait for network
                    return cached || fetchPromise;
                })
                .catch(() => {
                    // Offline fallback
                    return caches.match(request);
                })
        );
    }

    // Strategy 2: Static assets (Cache-First)
    else if (
        url.pathname.endsWith('.js') ||
        url.pathname.endsWith('.css') ||
        url.pathname.endsWith('.woff2') ||
        url.pathname.endsWith('.png') ||
        url.pathname.endsWith('.svg')
    ) {
        event.respondWith(
            caches.match(request)
                .then(cached => {
                    if (cached) {
                        return cached;
                    }

                    return fetch(request).then(response => {
                        if (response.ok) {
                            const clone = response.clone();
                            caches.open(STATIC_CACHE).then(cache => {
                                cache.put(request, clone);
                            });
                        }
                        return response;
                    });
                })
                .catch(() => {
                    // Static assets should be cached, return placeholder if not
                    console.warn('[SW] No cached response for:', request.url);
                })
        );
    }

    // Strategy 3: API calls (Network-First)
    else if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(RUNTIME_CACHE).then(cache => {
                            cache.put(request, clone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Return cached API response if available
                    return caches.match(request)
                        .catch(() => {
                            // No cache, offline
                            return new Response(
                                JSON.stringify({ error: 'Offline' }),
                                { status: 503, headers: { 'Content-Type': 'application/json' } }
                            );
                        });
                })
        );
    }
});

/**
 * Background Sync: Queue messages for later when offline
 */
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-messages') {
        event.waitUntil(
            // Sync queued messages when back online
            clients.matchAll().then(clientList => {
                clientList.forEach(client => {
                    client.postMessage({ type: 'BACKGROUND_SYNC', tag: event.tag });
                });
            })
        );
    }
});

console.log('[SW] Service Worker loaded');
