import os

dirs = [
    "backend",
    "frontend",
    "pipeline",
    "data/raw",
    "data/interim",
    "data/processed",
    "models",
    "docs",
    "scripts",
    "tests"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

with open(".gitignore", "w") as f:
    f.write("models/\ndata/raw/\ndata/interim/\n__pycache__/\n*.pyc\n.env\nvenv/\n")

print("Directories and .gitignore created successfully.")
