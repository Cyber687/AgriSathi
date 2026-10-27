path = 'services/local_gguf_translator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Tell the translator to look inside the llama.cpp folder as well
old_candidates = '''        candidates += [
            self.project_root / "models" / "sarvam-1-v0.5-Q8_0.gguf",
            self.project_root / "sarvam-1-v0.5-Q8_0.gguf",
        ]'''
        
new_candidates = '''        candidates += [
            self.project_root / "models" / "sarvam-1-v0.5-Q8_0.gguf",
            self.project_root / "llama.cpp" / "models" / "sarvam-1-v0.5-Q8_0.gguf", # <-- Added this line
            self.project_root / "sarvam-1-v0.5-Q8_0.gguf",
        ]'''

if old_candidates in content:
    content = content.replace(old_candidates, new_candidates)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Fixed path in local_gguf_translator.py!")
else:
    print("⚠️ Could not find the candidates block. Please check manually.")
