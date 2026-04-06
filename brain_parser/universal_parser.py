import os
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser

UNKNOWN_FILES = []

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())

LANGUAGE_MAP = {
    'python': PY_LANGUAGE,
    'javascript': JS_LANGUAGE,
}


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


def extract_functions(tree, code_bytes):
    # loop tree → find function_definition nodes → extract name and line number
    functions = []

    def walk(node):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                functions.append({
                    'name': code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8'),
                    'line': node.start_point[0] + 1
                })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return functions


def parse_file(filepath):
    filepath = os.path.abspath(filepath).replace("\\", "/")
    language = detect_language(filepath)

    # unknown files → log and return empty structure
    if language == 'unknown':
        return {
            'filepath': filepath,
            'language': 'unknown',
            'imports': [],
            'functions': [],
            'classes': [],
            'summary': 'unknown file - could not parse'
        }

    # read raw file content
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    code_bytes = content.encode('utf-8')
    functions = []

    # if language supported by tree-sitter → parse and extract functions
    if language in LANGUAGE_MAP:
        parser = Parser(LANGUAGE_MAP[language])
        tree = parser.parse(code_bytes)
        functions = extract_functions(tree, code_bytes)

    # TODO: extract classes
    # TODO: extract imports
    # TODO: summarize content using Groq → replace raw content with summary

    return {
        'filepath': filepath,
        'language': language,
        'imports': [],
        'functions': functions,
        'classes': [],
        'content': content
    }