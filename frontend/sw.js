
const CACHE_NAME = 'agrisathi-v1';
const ASSETS = [
  '/',
  '/frontend/style.css',
  '/frontend/script.js',
  '/frontend/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request))
  );
});
