import os
import sys
import re

def check_design_rules():
    failed = False
    
    # 1. Template leftovers check
    template_files = [
        "frontend/src/assets/hero.png",
        "frontend/src/assets/react.svg",
        "frontend/src/assets/vite.svg",
        "frontend/src/App.css"
    ]
    for tf in template_files:
        if os.path.exists(tf):
            print(f"Error: Template leftover file found: {tf}")
            failed = True
            
    # Check index.html title
    index_html_path = "frontend/index.html"
    if os.path.exists(index_html_path):
        with open(index_html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
            if title_match:
                title_text = title_match.group(1).strip()
                if title_text.lower() == "frontend" or "vite" in title_text.lower():
                    print(f"Error: Invalid template title '{title_text}' found in {index_html_path}")
                    failed = True

    # 2. Hardcoded localhost / 127.0.0.1 in frontend source
    frontend_src = "frontend/src"
    if os.path.exists(frontend_src):
        for root, _, files in os.walk(frontend_src):
            for file in files:
                if file.endswith((".js", ".jsx", ".ts", ".tsx", ".html", ".css")):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, 1):
                            if "127.0.0.1" in line:
                                print(f"Error in {filepath}:{line_no} - Hardcoded '127.0.0.1' in frontend source")
                                failed = True
                            if "localhost" in line:
                                print(f"Error in {filepath}:{line_no} - Hardcoded 'localhost' in frontend source")
                                failed = True

    # 3. Em dashes in any source or documentation file
    dirs_to_check = ["src", "backend", "scripts", "tests", "docs", "frontend/src", "frontend/index.html", "README.md"]
    banned_words = [
        "made with ai", "lorem", "todo", "fixme", 
        "unlock", "empower", "seamless", "revolutionize", 
        "cutting-edge", "game-changing", "harness the power", 
        "leverage", "supercharge", "next-generation", 
        "in today's fast-paced world"
    ]
    banned_regexes = [
        (r'from-purple-|via-violet-|to-indigo-', "Purple/violet gradient classes"),
        (r'rounded-full\b.*(?:button|btn|<button)', "Pill-shaped button (rounded-full)"),
    ]
    emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]', flags=re.UNICODE)

    checked_files = set()
    for d in dirs_to_check:
        if not os.path.exists(d):
            continue
        if os.path.isfile(d):
            checked_files.add(d)
        else:
            for root, _, files in os.walk(d):
                # Ignore node_modules, .git, __pycache__, .pytest_cache
                if any(ignored in root for ignored in ["node_modules", ".git", "__pycache__", ".pytest_cache"]):
                    continue
                for f in files:
                    if f.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.md', '.css', '.json', '.yaml', '.yml')):
                        # Skip binary or auto-generated json if large
                        checked_files.add(os.path.join(root, f))

    for filepath in sorted(checked_files):
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_no, line in enumerate(f, 1):
                    # Check for em dash (U+2014)
                    if "\u2014" in line:
                        print(f"Error in {filepath}:{line_no} - Em dash (U+2014) found")
                        failed = True
                    
                    line_lower = line.lower()
                    # Banned words
                    for word in banned_words:
                        if word in line_lower:
                            # Skip if word is in check_design_rules.py definition itself
                            if "check_design_rules.py" in filepath:
                                continue
                            print(f"Error in {filepath}:{line_no} - Banned word/phrase found: '{word}'")
                            failed = True
                            
                    # Banned styles
                    for pattern, desc in banned_regexes:
                        if re.search(pattern, line_lower):
                            if "check_design_rules.py" in filepath:
                                continue
                            print(f"Error in {filepath}:{line_no} - {desc} found.")
                            failed = True
                            
                    # Emojis
                    if emoji_pattern.search(line):
                        print(f"Error in {filepath}:{line_no} - Emoji found.")
                        failed = True
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            failed = True

    if failed:
        print("\nDesign rules check FAILED!")
        sys.exit(1)
    else:
        print("\nAll design rules passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    check_design_rules()
