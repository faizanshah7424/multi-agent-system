import os
import ast
import sys

def get_stdlib_modules():
    if hasattr(sys, 'stdlib_module_names'):
        return set(sys.stdlib_module_names)
    # fallback stdlib list
    return {
        'os', 'sys', 'ast', 'json', 'time', 'datetime', 'math', 'random', 're',
        'typing', 'collections', 'functools', 'itertools', 'pathlib', 'asyncio',
        'logging', 'unittest', 'dataclasses', 'uuid', 'shutil', 'subprocess',
        'traceback', 'inspect', 'importlib', 'tempfile', 'copy', 'hashlib',
        'base64', 'enum', 'threading', 'queue', 'signal', 'socket', 'http', 'urllib',
        'pkgutil', 'typing_extensions', 'contextlib', 'platform', 'string', 'select'
    }

root_dir = os.path.abspath(r"E:\multi-agent-system")
ignore_dirs = {'.venv', 'venv', '.git', 'worktrees', '__pycache__', 'node_modules', 'dashboard', 'scratch'}

local_modules = set()
for item in os.listdir(root_dir):
    full_path = os.path.join(root_dir, item)
    if os.path.isdir(full_path):
        local_modules.add(item)
    elif item.endswith('.py'):
        local_modules.add(item[:-3])

stdlib_modules = get_stdlib_modules()

imports_found = {} # top_level_import -> list of (file, line_no)

for dirpath, dirnames, filenames in os.walk(root_dir):
    # prune ignore dirs
    dirnames[:] = [d for d in dirnames if d not in ignore_dirs and not d.startswith('.')]
    
    for fname in filenames:
        if fname.endswith('.py'):
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root_dir)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    tree = ast.parse(f.read(), filename=fpath)
                
                for node in ast.walk(tree):
                    mod_name = None
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            mod_name = alias.name.split('.')[0]
                            if mod_name:
                                imports_found.setdefault(mod_name, []).append((rel_path, node.lineno))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.level == 0:
                            mod_name = node.module.split('.')[0]
                            if mod_name:
                                imports_found.setdefault(mod_name, []).append((rel_path, node.lineno))
            except Exception as e:
                print(f"Error parsing {rel_path}: {e}")

third_party = {}
for mod, occurrences in sorted(imports_found.items()):
    if mod in stdlib_modules:
        continue
    if mod in local_modules:
        continue
    third_party[mod] = occurrences

print("--- THIRD PARTY IMPORTS FOUND ---")
for mod, occurrences in sorted(third_party.items()):
    files = sorted(set(f"{f}:{l}" for f, l in occurrences))
    print(f"\nModule: {mod}")
    print(f"  Count: {len(occurrences)}")
    print(f"  Sample usage: {files[:5]}")
