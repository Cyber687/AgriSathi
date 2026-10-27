path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the exact class and __init__ definition
old_init = """class AgriSathiApplication:
    \"\"\"Initialize and connect AgriSathi components.\"\"\"

    def __init__(self):
        self.knowledge_base = AgriSathiKnowledgeBase("""

new_init = """class AgriSathiApplication:
    \"\"\"Initialize and connect AgriSathi components.\"\"\"

    def __init__(self):
        # UPGRADE: Initialize Cache & Memory
        self.response_cache = {}
        self.last_crop_context = None
        
        self.knowledge_base = AgriSathiKnowledgeBase("""

if old_init in content:
    content = content.replace(old_init, new_init)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Successfully injected response_cache and last_crop_context into __init__!")
else:
    print("⚠️ Could not find the exact __init__ block. Trying regex...")
    import re
    content = re.sub(
        r'(def __init__\(self\):\n)',
        r'\1        self.response_cache = {}\n        self.last_crop_context = None\n',
        content,
        count=1
    )
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Regex fix applied!")
