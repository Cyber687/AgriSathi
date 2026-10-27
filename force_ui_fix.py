import re

# --- FIX 1: Force Browser Cache Refresh in HTML ---
html_path = 'frontend/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Add ?v=2 to force the browser to download the new files
html = html.replace('href="/frontend/style.css"', 'href="/frontend/style.css?v=2"')
html = html.replace('src="/frontend/script.js"', 'src="/frontend/script.js?v=2"')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print("✅ index.html patched: Browser cache busted.")

# --- FIX 2: Hard Replace the CSS ---
css_path = 'frontend/style.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Replace the old blocky green highlight with a sleek left border
pattern = r'\.nav-item\.active\s*\{[^}]*\}'
new_css = """.nav-item.active {
    background: rgba(46, 125, 50, 0.1); /* Subtle transparent green */
    color: var(--green-700);
    border-left: 4px solid var(--green-600);
    border-radius: 0 11px 11px 0;
    margin-left: -4px;
    padding-left: 16px;
    font-weight: 700;
}"""

css = re.sub(pattern, new_css, css)
with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)
print("✅ style.css hard replaced.")

# --- FIX 3: Hard Replace the JS Logic ---
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Regex to find the exact nav-item click listener block
pattern = r'\$\$\("\.nav-item"\)\.forEach\(button => \{.*?\n\}\);'
new_js = """$$(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        // If it's a Workspace tab (AI Assistant, Weather, Mandi)
        if (button.dataset.view) {
            $$(".nav-item").forEach(item => item.classList.remove("active"));
            button.classList.add("active");
            
            const view = button.dataset.view;
            if (view === "chat") scrollToChat();
            else if (view === "weather") { 
                $("#temperature").scrollIntoView({ behavior: "smooth", block: "center" }); 
                if (state.location) loadWeather(); 
            }
            else if (view === "mandi") {
                elements.mandiPrice.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        } 
        // If it's a Farming Tool (Crop Guidance, Pest Management, etc.)
        else if (button.dataset.question) {
            // Keep "AI Assistant" as the active tab
            $$(".nav-item").forEach(item => item.classList.remove("active"));
            const chatTab = document.querySelector('.nav-item[data-view="chat"]');
            if (chatTab) chatTab.classList.add("active");
            
            // Type the question and scroll to chat
            elements.questionInput.value = button.dataset.question;
            updateCharacterCount(); 
            scrollToChat();
        }
        elements.sidebar.classList.remove("open");
    });
});"""

js = re.sub(pattern, new_js, js, flags=re.DOTALL)
with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ script.js hard replaced.")
