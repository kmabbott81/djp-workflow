/**
 * Service Worker for PWA offline support
 * Caches artifacts for offline viewing
 */

const CACHE_NAME = 'djp-workflows-v1';
const OFFLINE_CACHE = 'djp-offline-v1';

// Feature flag for offline mode
const OFFLINE_ENABLED = true; // Set via build config

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/manifest.json',
  '/pwa/icons/icon-192x192.png',
  '/pwa/icons/icon-512x512.png',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );

  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== OFFLINE_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );

  self.clients.claim();
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (!request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        console.log('[SW] Serving from cache:', request.url);
        return cachedResponse;
      }

      // Fetch from network
      return fetch(request)
        .then((response) => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Cache artifacts for offline viewing
          if (OFFLINE_ENABLED && request.url.includes('/artifacts/')) {
            const responseToCache = response.clone();
            caches.open(OFFLINE_CACHE).then((cache) => {
              console.log('[SW] Caching artifact:', request.url);
              cache.put(request, responseToCache);
            });
          }

          return response;
        })
        .catch((error) => {
          console.error('[SW] Fetch failed:', error);

          // Return offline page if available
          return caches.match('/offline.html').then((offlineResponse) => {
            return offlineResponse || new Response('Offline - content unavailable', {
              status: 503,
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'text/plain' },
            });
          });
        });
    })
  );
});

// Message event - handle commands from main thread
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => {
      event.ports[0].postMessage({ success: true });
    });
  }
});
