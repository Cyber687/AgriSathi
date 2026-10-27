import re
import json
import os

# --- CHERRY 1 & 3: Add WhatsApp Share & Copy Toast to script.js ---
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Update the message actions block to include WhatsApp
old_actions = """        const speakButton = document.createElement("button");
        speakButton.type = "button"; speakButton.textContent = "Read aloud";
        speakButton.addEventListener("click", () => speakText(String(text ?? "")));
        
        actions.append(copyButton, speakButton);"""

new_actions = """        const speakButton = document.createElement("button");
        speakButton.type = "button"; speakButton.textContent = "Read aloud";
        speakButton.addEventListener("click", () => speakText(String(text ?? "")));

        // CHERRY: WhatsApp Share Button
        const waButton = document.createElement("button");
        waButton.type = "button"; 
        waButton.textContent = "Share 📲";
        waButton.style.color = "#25D366"; // WhatsApp Green
        waButton.addEventListener("click", () => {
            const shareText = encodeURIComponent(`AgriSathi Advisory:\\n\\n${String(text ?? "")}\\n\\n(Courtesy of AgriSathi AI)`);
            window.open(`https://wa.me/?text=${shareText}`, '_blank');
        });
        
        actions.append(copyButton, speakButton, waButton);"""

js = js.replace(old_actions, new_actions)

# Improve the copy toast message
js = js.replace('showToast(t("copied"));', 'showToast("✅ Answer copied to clipboard!");')

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ Added WhatsApp Share & Copy Toast!")

# --- CHERRY 2: PWA Support (Manifest & Service Worker) ---
# Create manifest.json
manifest_data = {
    "name": "AgriSathi - AI Farming Assistant",
    "short_name": "AgriSathi",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#174b34",
    "theme_color": "#174b34",
    "description": "Offline AI agricultural advisory for Indian farmers.",
    "icons": [
        {
            "src": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxOTIiIGhlaWdodD0iMTkyIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PGNpcmNsZSBjeD0iNTAiIGN5PSI1MCIgcj0iNTAiIGZpbGw9IiMxNzRiMzQiLz48dGV4dCB4PSI1MCIgeT0iNTUiIGZvbnQtc2l6ZT0iNTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiPvCfjLE8L3RleHQ+PC9zdmc+",
            "sizes": "192x192",
            "type": "image/svg+xml"
        }
    ]
}
with open('frontend/manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest_data, f, indent=2)
print("✅ Created manifest.json")

# Create service worker (sw.js)
sw_code = """
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
"""
with open('frontend/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_code)
print("✅ Created sw.js (Service Worker)")

# Update index.html to link the manifest and register the service worker
html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add manifest link to <head>
if '<link rel="manifest"' not in html:
    html = html.replace('</head>', '    <link rel="manifest" href="/frontend/manifest.json">\n    <meta name="theme-color" content="#174b34">\n</head>')

# Add service worker registration before </body>
if 'navigator.serviceWorker' not in html:
    html = html.replace('</body>', '''<script>
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/frontend/sw.js');
        });
    }
</script>
</body>''')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ Updated index.html for PWA!")
