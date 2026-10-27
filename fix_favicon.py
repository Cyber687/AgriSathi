import os

# 1. Create a custom SVG favicon with your green leaf logo
favicon_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <circle cx="50" cy="50" r="50" fill="#174b34" />
  <text x="50" y="55" font-size="55" text-anchor="middle" dominant-baseline="middle">🌱</text>
</svg>'''

os.makedirs('frontend', exist_ok=True)
with open('frontend/favicon.svg', 'w', encoding='utf-8') as f:
    f.write(favicon_svg)
print("✅ Created custom favicon.svg")

# 2. Link the favicon in index.html
html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Inject the favicon link into the <head>
if '<link rel="icon"' not in html:
    html = html.replace(
        '<link rel="manifest" href="/frontend/manifest.json">',
        '<link rel="icon" type="image/svg+xml" href="/frontend/favicon.svg">\n    <link rel="manifest" href="/frontend/manifest.json">'
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ index.html patched: Favicon linked!")
else:
    print("✅ Favicon already linked.")
