import os

UNKNOWN_FILES = []


def detect_language(filepath):
    filepath = os.path.abspath(filepath).replace("\\", "/")
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rb': 'ruby',
        '.cpp': 'cpp',
        '.cs': 'csharp',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.sql': 'sql',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.rs': 'rust',
        '.c': 'c',
        '.sh': 'shell',
        '.env': 'env',
        '.xml': 'xml',
        '.toml': 'toml',
    }
    ext = os.path.splitext(filepath)[1].lower()
    language = ext_map.get(ext, 'unknown')

    if language == 'unknown':
        UNKNOWN_FILES.append(filepath)

    return language


def parse_file(filepath):
    language = detect_language(filepath)
    filepath = os.path.abspath(filepath).replace("\\", "/")

    if language == 'unknown':
        return {
            'filepath': filepath,
            'language': 'unknown',
            'imports': [],
            'functions': [],
            'classes': [],
            'summary': 'unknown file - could not parse'
        }

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    return {
        'filepath': filepath,
        'language': language,
        'imports': [],
        'functions': [],
        'classes': [],
        'content': content  # tree-sitter fills imports/functions next
    }