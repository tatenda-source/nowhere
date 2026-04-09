const CACHE_NAME = 'nowhere-v1';
const PRECACHE_URLS = ['/', '/offline.html'];

// Patterns that must never be cached
const NO_CACHE_PATTERNS = ['/api/', '/auth/', '/intents/', '/ws/', '/health', '/metrics'];

// Static asset extensions eligible for cache-first
const STATIC_EXTENSIONS = /\.(js|css|png|jpg|jpeg|svg|woff|woff2|ico|webp)$/;

// ─── Install: pre-cache app shell ────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

// ─── Activate: purge old caches ──────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ─── Fetch: route requests to the right strategy ─────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip WebSocket upgrades
  if (request.headers.get('Upgrade') === 'websocket') return;

  // Skip API / auth / WS / health / metrics — never cache these
  if (NO_CACHE_PATTERNS.some((p) => url.pathname.includes(p))) return;

  // Skip cross-origin requests (CDN analytics, third-party scripts, etc.)
  if (url.origin !== self.location.origin) return;

  // Navigation requests (HTML pages): Network First -> cached / -> offline.html
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() =>
          caches.match(request).then(
            (cached) => cached || caches.match('/offline.html')
          )
        )
    );
    return;
  }

  // Static assets: Cache First -> network (and update cache)
  if (STATIC_EXTENSIONS.test(url.pathname)) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
            return response;
          })
      )
    );
    return;
  }

  // Everything else: Network First -> cache fallback
  event.respondWith(
    fetch(request)
      .then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        return response;
      })
      .catch(() => caches.match(request))
  );
});
