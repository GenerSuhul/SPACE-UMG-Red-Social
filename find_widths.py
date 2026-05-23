import os
import re

workspace_dir = r"c:\Users\itagr\.gemini\antigravity\scratch\Red-Social"
found = []
for root, dirs, files in os.walk(workspace_dir):
    for file in files:
        if file.endswith((".css", ".scss")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Find any width: or max-width: styles
                    matches = re.findall(r"([^{]*\{[^}]*(?:width|max-width)\s*:\s*[^;]+;[^}]*\})", content)
                    if matches:
                        found.append((path, matches))
            except Exception as e:
                pass

print("Occurrences of width / max-width in CSS/SCSS:")
for path, matches in found:
    print(f"\nFile: {path}")
    for m in matches[:10]: # limit to first 10
        cleaned = " ".join(m.split())
        print(f"  {cleaned}")
