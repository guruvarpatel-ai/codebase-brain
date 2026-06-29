import os
import json
from brain_parser.universal_parser import parse_file

SKIP_FOLDERS = {
    'lib', '.idea', '__pycache__',
    'codebase_brain.egg-info', 'node_modules',
    '.git', 'venv', '.env', 'tests', 'temp'
}
SKIP_FILES = {
    'brain.json', 'brain_map.html'
}
def should_skip(path):
    parts = path.replace('\\', '/').split('/')
    for part in parts:
        if part in SKIP_FOLDERS:
            return True
    return False
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

def get_brain_path():
    """Always returns brain.json in the current working directory."""
    return os.path.join(os.getcwd(), 'brain.json')

def save_brain(brain, output_path=None):
    if output_path is None:
        output_path = get_brain_path()
    with open(output_path, "w") as f:
        json.dump(brain, f, indent=4)
    print(f"Brain saved to {output_path}")

def load_brain(output_path=None):
    if output_path is None:
        output_path = get_brain_path()
    if not os.path.exists(output_path):
        return None
    with open(output_path, 'r') as f:
        return json.load(f)


def summarize_high_risk_files(brain, risk):
    from brain_parser.universal_parser import summarize_file

    summarized = 0
    for filepath, data in brain.items():
        file_risk = risk.get(filepath, 'LOW')
        content = data.get('content', '')

        if file_risk == 'HIGH' and content:
            print(f"Summarizing HIGH risk file: {filepath}")
            data['summary'] = summarize_file(filepath, content, data.get('language', ''))
            data.pop('content', None)
            summarized += 1
        else:
            # low/medium risk - generate simple summary from structure
            functions = [f['name'] for f in data.get('functions', [])]
            classes = [c['name'] for c in data.get('classes', [])]
            imports = [i['name'] for i in data.get('imports', [])]
            data[
                'summary'] = f"File with {len(functions)} functions: {', '.join(functions[:5])}. Classes: {', '.join(classes[:3])}. Imports: {', '.join(imports[:5])}"
            data.pop('content', None)

    print(f"Summarized {summarized} HIGH risk files with Groq. Rest used structure only.")
    return brain

if __name__ == "__main__":
    brain = walk_codebase(".")
    save_brain(brain)

    loaded = load_brain()
    print(f"Brain loaded with {len(loaded)} files")