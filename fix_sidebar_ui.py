import re

# --- FIX 1: Clean up the CSS ---
css_path = 'frontend/style.css'
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Remove the old heavy green block styling
old_css = """.nav-item.active {
    background: var(--green-100);
    color: var(--green-900);
}"""

# Add a sleek left-border indicator instead
new_css = """.nav-item {
    border-left: 3px solid transparent; /* Placeholder for smooth transition */
    border-radius: 0 11px 11px 0; /* Adjust radius for the left border */
    margin-left: -3px; /* Pull it flush with the edge */
}

.nav-item.active {
    background: var(--green-50);
    color: var(--green-800);
    border-left: 3px solid var(--green-600);
    font-weight: 700;
}

/* Make sure the dark mode looks good too */
body.dark-mode .nav-item.active {
    background: var(--surface-soft);
    color: var(--green-100);
}"""

css = css.replace(old_css, new_css)
with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)
print("✅ style.css patched: Sleek left-border active state added.")

# --- FIX 2: Fix the JavaScript active state logic ---
js_path = 'frontend/script.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the navigation click logic
old_nav = """$$(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        $$(".nav-item").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        const view = button.dataset.view;
        if (view === "chat") scrollToChat();
        else if (view === "weather") { $("#temperature").scrollIntoView({ behavior: "smooth", block: "center" }); if (state.location) loadWeather(); }
        else if (view === "mandi") elements.mandiPrice.scrollIntoView({ behavior: "smooth", block: "center" });
        if (button.dataset.question) { elements.questionInput.value = button.dataset.question; updateCharacterCount(); scrollToChat(); }
        elements.sidebar.classList.remove("open");
    });
});"""

new_nav = """$$(".nav-item").forEach(button => {
    button.addEventListener("click", () => {
        // If it's a Workspace tab (view), switch the active highlight
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
        // If it's a Farming Tool (question), auto-switch to the "AI Assistant" tab
        else if (button.dataset.question) {
            // Make sure "AI Assistant" is the active green tab
            $$(".nav-item").forEach(item => item.classList.remove("active"));
            const chatTab = document.querySelector('.nav-item[data-view="chat"]');
            if (chatTab) chatTab.classList.add("active");
            
            // Fill the input and scroll to chat
            elements.questionInput.value = button.dataset.question;
            updateCharacterCount(); 
            scrollToChat();
        }
        elements.sidebar.classList.remove("open");
    });
});"""

js = js.replace(old_nav, new_nav)
with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("✅ script.js patched: Active state fixed. No more double-green highlighting.")
