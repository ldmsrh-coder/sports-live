/* Sports Live service worker.
 * Same-origin shell only. Never cache third-party feeds, credentials, or POST requests.
 * Network-first keeps scores fresh; cached data is an offline fallback, not a live result.
 */
const CACHE_PREFIX = 'sports-live-shell-';
const CACHE_VERSION = '20261022-18';
const CACHE_NAME = CACHE_PREFIX + CACHE_VERSION;
const BASE = new URL('./', self.location.href);
const SHELL = [
  new URL('./', BASE).href,
  new URL('./index.html', BASE).href,
  new URL('./app.js?v=20261022-pwa-countryfix-18', BASE).href,
  new URL('./manifest.webmanifest', BASE).href,
  new URL('./data/korean-sports.json', BASE).href,
  new URL('./icons/sports-live.svg', BASE).href
];
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.all(SHELL.map(async url => {
      try {
        const response = await fetch(url, {cache: 'reload'});
        if (response.ok && response.type === 'basic') await cache.put(url, response);
      } catch (_) { /* Offline-first installation may still proceed with a partial shell. */ }
    }));
    await self.skipWaiting();
  })());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  const isNavigation = request.mode === 'navigate';
  const path = url.pathname;
  const isShellAsset = /\.(?:js|css|json|webmanifest|svg|png|ico)$/i.test(path) || path === BASE.pathname;
  if (!isNavigation && !isShellAsset) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    try {
      const response = await fetch(request);
      if (response && response.ok && response.type === 'basic') {
        const key = isNavigation ? new URL('./index.html', BASE).href : request.url;
        await cache.put(key, response.clone());
      }
      return response;
    } catch (_) {
      const cached = await cache.match(request, {ignoreSearch: true});
      if (cached) return cached;
      if (isNavigation) {
        const fallback = await cache.match(new URL('./index.html', BASE).href);
        if (fallback) return fallback;
      }
      return new Response('오프라인 상태입니다. 인터넷 연결 후 다시 시도해 주세요.', {
        status: 503, headers: {'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store'}
      });
    }
  })());
});
self.addEventListener('message', event => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
