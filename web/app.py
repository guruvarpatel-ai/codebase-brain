from flask import Flask, request, jsonify, render_template
import os
import shutil
import stat
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_parser.codebase_walker import walk_codebase, save_brain, summarize_high_risk_files, load_brain
from brain_parser.graph_builder import build_graph, calculate_risk, get_impact
from brain_parser.bug_detector import run_all_detectors

app = Flask(__name__, static_folder='static', template_folder='templates')


def clean_path(filepath, temp_path):
    clean = filepath.replace('\\', '/')
    temp = temp_path.replace('\\', '/')
    if temp in clean:
        clean = clean.split(temp)[-1].lstrip('/')
    return clean


def force_delete(path):
    if not os.path.exists(path):
        return
    def handle_error(func, path, exc):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass
    try:
        shutil.rmtree(path, onerror=handle_error)
    except Exception as e:
        print(f"Warning: Could not delete {path}: {e}")


def get_brain_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain.json')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    github_url = data.get('url', '').strip()

    if not github_url:
        return jsonify({'error': 'No URL provided'}), 400

    if not github_url.startswith('https://github.com/'):
        return jsonify({'error': 'Invalid GitHub URL'}), 400

    repo_name = github_url.split('/')[-1].replace('.git', '')
    temp_path = os.path.join(os.path.dirname(__file__), 'temp', repo_name)

    force_delete(temp_path)

    try:
        result = subprocess.run(
            ['git', 'clone', '--depth=1', github_url, temp_path],
            capture_output=True, timeout=120, text=True
        )
        if result.returncode != 0:
            return jsonify({'error': f'Clone failed: {result.stderr}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Clone timed out. Try a smaller repo.'}), 500
    except Exception as e:
        return jsonify({'error': f'Clone error: {str(e)}'}), 500

    try:
        brain = walk_codebase(temp_path)
        G = build_graph(brain)
        risk = calculate_risk(G)
        brain = summarize_high_risk_files(brain, risk)
        bugs = run_all_detectors(brain, G, temp_path=temp_path)
        save_brain(brain, get_brain_path())

        for bug in bugs:
            if 'file' in bug:
                clean = clean_path(bug['file'], temp_path)
                bug['file'] = clean
                if 'message' in bug:
                    parts = bug['message'].split(': ', 1)
                    if len(parts) > 1:
                        bug['message'] = f"Security risk in {clean}: {parts[1]}"
                    else:
                        bug['message'] = parts[0]
            if 'files' in bug:
                bug['files'] = [clean_path(f, temp_path) for f in bug['files']]

        files = []
        for filepath, fdata in brain.items():
            files.append({
                'path': clean_path(filepath, temp_path),
                'language': fdata.get('language'),
                'functions': len(fdata.get('functions', [])),
                'classes': len(fdata.get('classes', [])),
                'summary': fdata.get('summary', ''),
                'risk': risk.get(filepath, 'LOW')
            })

        return jsonify({
            'repo': repo_name,
            'total_files': len(brain),
            'files': files,
            'bugs': bugs
        })

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    finally:
        force_delete(temp_path)


@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    from brain_parser.query_engine import ask_brain
    answer = ask_brain(question)
    return jsonify({'answer': answer})


@app.route('/impact', methods=['POST'])
def impact():
    data = request.json
    filename = data.get('filename', '').strip()
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    brain = load_brain(get_brain_path())
    if not brain:
        return jsonify({'error': 'No brain found. Analyze a repo first.'}), 400

    G = build_graph(brain)
    risk = calculate_risk(G)

    matched = None
    filename_norm = filename.replace('\\', '/').lower()
    for key in G.nodes():
        key_norm = key.replace('\\', '/').lower()
        if key_norm.endswith(filename_norm):
            matched = key
            break

    if not matched:
        return jsonify({'error': f'File not found: {filename}'}), 404

    result = get_impact(G, matched)
    if not result:
        return jsonify({'error': f'File not found: {filename}'}), 404

    def clean(path):
        p = path.replace('\\', '/')
        idx = p.find('/temp/')
        if idx != -1:
            after_temp = p[idx + 6:]
            parts = after_temp.split('/', 1)
            if len(parts) > 1:
                return parts[1]
            return parts[0]
        return p

    return jsonify({
        'target': clean(matched),
        'risk': risk.get(matched, 'LOW'),
        'direct': [clean(f) for f in result['direct']],
        'indirect': [clean(f) for f in result['indirect']],
        'total_affected': result['total_affected']
    })


if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'temp'), exist_ok=True)
    app.run(debug=False, port=5000)