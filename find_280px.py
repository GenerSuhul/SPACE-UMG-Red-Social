import os

workspace_dir = r"c:\Users\itagr\.gemini\antigravity\scratch\Red-Social"
found = []
for root, dirs, files in os.walk(workspace_dir):
    for file in files:
        if file.endswith((".css", ".scss", ".ts", ".html")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "280px" in content:
                        found.append(path)
            except Exception as e:
                pass

print("Occurrences of 280px found in:")
for path in found:
    print(f"  {path}")
