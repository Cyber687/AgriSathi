import re

# --- PATCH 1: index.html (Remove backend text, add disclaimer) ---
html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Hide the "AgriSathi backend" text
html = html.replace('<p>AgriSathi backend</p>', '<p>Status</p>')

# Add a professional disclaimer above the input
old_disclaimer = '''<div class="chat-disclaimer">
                        <span>ⓘ</span>
                        Agricultural guidance depends on local conditions.
                        Check sources and follow applicable official advice.
                    </div>'''
new_disclaimer = '''<div class="chat-disclaimer" style="background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 0.9em;">
                        <span>⚠️</span>
                        <strong>Important:</strong> This AI provides information based on official databases. It does not replace professional agronomic advice. Always consult your local KVK before applying chemicals.
                    </div>'''
html = html.replace(old_disclaimer, new_disclaimer)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print('✅ index.html patched: Professional status & disclaimer added.')

# --- PATCH 2: script.js (Show "Thinking..." while waiting for LLM) ---
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Change the connection text to just show a dot
js = js.replace('elements.connectionText.textContent = connected ? "Online" : "Offline";', 'elements.connectionText.textContent = connected ? "Active" : "Offline";')

# Update typing indicator text
js = js.replace('"<span>Sending...</span><span>⌛</span>"', '"<span>AgriSathi is thinking...</span><span>⌛</span>"')

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print('✅ script.js patched: Improved loading indicators.')
