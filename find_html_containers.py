import os

workspace_dir = r"c:\Users\itagr\.gemini\antigravity\scratch\Red-Social"
found = []
for root, dirs, files in os.walk(workspace_dir):
    for file in files:
        if file.endswith(".html"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if "page-container" in line or "page-wrapper" in line:
                            found.append((path, i, line.strip()))
            except Exception as e:
                pass

print("Occurrences of page-container / page-wrapper:")
for path, line_no, content in found:
    print(f"  {path}:{line_no}: {content}")
