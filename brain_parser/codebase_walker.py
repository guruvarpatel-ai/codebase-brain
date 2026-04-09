import os
import json
from brain_parser.universal_parser import parse_file

SKIP_FOLDERS = {
    'flask', 'lib', '.idea', '__pycache__',
    'codebase_brain.egg-info', 'node_modules',
    '.git', 'venv', '.env', 'tests'
}
SKIP_FILES = {
    'brain.json', 'brain_map.html'
}
def walk_codebase(root_path):
    # load existing brain to check hashes
    existing_brain = load_brain() or {}
    brain = {}

    for folder, subfolders, files in os.walk(root_path):
        subfolders[:] = [s for s in subfolders if s not in SKIP_FOLDERS]

        for file in files:
            if file in SKIP_FILES:
                continue

            full_path = os.path.join(folder, file)

            # read content to generate hash
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except:
                continue

            from brain_parser.universal_parser import get_file_hash
            current_hash = get_file_hash(content)

            # if file exists in brain and hash matches → skip re-parsing
            if full_path in existing_brain:
                if existing_brain[full_path].get('hash') == current_hash:
                    brain[full_path] = existing_brain[full_path]
                    continue

            # file is new or changed → parse and summarize
            result = parse_file(full_path)
            if result is not None and result['language'] != 'unknown':
                brain[full_path] = result

    return brain

BRAIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'brain.json')

def save_brain(brain, output_path=BRAIN_PATH):
    with open(output_path, "w") as f:
        json.dump(brain, f, indent=4)
    print(f"Brain saved to {output_path}")

def load_brain(input_path=BRAIN_PATH):
    if not os.path.exists(input_path):
        print("No brain found. Run walker first.")
        return None
    with open(input_path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    brain = walk_codebase(".")
    save_brain(brain)

    loaded = load_brain()
    print(f"Brain loaded with {len(loaded)} files")