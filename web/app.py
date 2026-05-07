from flask import Flask, request, jsonify, render_template
import os
import subprocess
import shutil
import stat
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain_parser.codebase_walker import walk_codebase, save_brain
from brain_parser.graph_builder import build_graph, calculate_risk
from brain_parser.bug_detector import run_all_detectors

app = Flask(__name__, static_folder='static', template_folder='templates')

def clean_path(filepath, temp_path):
    # strip temp folder prefix → show relative path only
    clean = filepath.replace('\\', '/')
    temp = temp_path.replace('\\', '/')
    if temp in clean:
        clean = clean.split(temp)[-1].lstrip('/')
    return clean

def force_delete(path):
    # force delete on Windows — handles read-only git files
    def handle_error(func, path, exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if os.path.exists(path):
        shutil.rmtree(path, onerror=handle_error)

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

    # clean up old clone
    force_delete(temp_path)

    # clone repo
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

    # analyze
    try:
        brain = walk_codebase(temp_path)
        brain_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'brain.json')
        save_brain(brain, brain_json_path)
        G = build_graph(brain)
        bugs = run_all_detectors(brain, G)
        # clean bug file paths
        for bug in bugs:
            if 'file' in bug:
                clean = clean_path(bug['file'], temp_path)
                bug['file'] = clean
                if 'message' in bug:
                    # rebuild message with clean path
                    bug['message'] = bug['message'].split(': ', 1)
                    if len(bug['message']) > 1:
                        bug['message'] = f"Security risk in {clean}: {bug['message'][1]}"
                    else:
                        bug['message'] = bug['message'][0]
            if 'files' in bug:
                bug['files'] = [clean_path(f, temp_path) for f in bug['files']]
        risk = calculate_risk(G)

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

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '').strip()
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    from brain_parser.query_engine import ask_brain
    answer = ask_brain(question)
    return jsonify({'answer': answer})

if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'temp'), exist_ok=True)
    app.run(debug=False, port=5000)