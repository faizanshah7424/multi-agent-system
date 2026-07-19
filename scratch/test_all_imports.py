import os
import sys
import ast

root_dir = os.path.abspath(r"E:\multi-agent-system")
ignore_dirs = {'.venv', 'venv', '.git', 'worktrees', '__pycache__', 'node_modules', 'dashboard', 'scratch', 'tests', 'examples'}

# Direct static import test of modules by loading top level AST imports
missing_packages = {}

for dirpath, dirnames, filenames in os.walk(root_dir):
    dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
    
    for fname in filenames:
        if fname.endswith('.py'):
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root_dir)
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            try:
                tree = ast.parse(content, filename=fpath)
            except Exception:
                continue

            for node in ast.walk(tree):
                mod_name = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod_name = alias.name.split('.')[0]
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.level == 0:
                        mod_name = node.module.split('.')[0]
                
                if mod_name:
                    try:
                        __import__(mod_name)
                    except ModuleNotFoundError as err:
                        if err.name:
                            missing_packages.setdefault(err.name, set()).add(f"{rel_path}:{node.lineno}")

print("--- MISSING MODULES FOUND BY ATTEMPTING IMPORTS ---")
for mod, files in sorted(missing_packages.items()):
    print(f"\nMissing module: {mod}")
    print(f"Used in {len(files)} location(s):")
    for file in sorted(files)[:5]:
        print(f"  - {file}")
