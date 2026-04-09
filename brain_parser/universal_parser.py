import os
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
import tree_sitter_java as tsjava
import tree_sitter_typescript as tstypescript
import hashlib
from tree_sitter import Language, Parser


UNKNOWN_FILES = []

PY_LANGUAGE = Language(tspython.language())
JS_LANGUAGE = Language(tsjavascript.language())
JAVA_LANGUAGE=Language(tsjava.language())
TS_LANGUAGE = Language(tstypescript.language_typescript())

LANGUAGE_MAP = {
    'python': PY_LANGUAGE,
    'javascript': JS_LANGUAGE,
    'java': JAVA_LANGUAGE,
    'typescript':TS_LANGUAGE
}
FUNCTION_NODES = {
    'python': ['function_definition'],
    'javascript': ['function_declaration', 'arrow_function', 'function_expression'],
    'java': ['method_declaration'],
'typescript': ['function_declaration', 'arrow_function', 'function_expression'],
}
CLASS_NODES = {
    'python': ['class_definition'],
    'javascript': ['class_declaration'],
    'java': ['class_declaration'],
    'typescript': ['class_declaration'],

}
IMPORT_NODES = {
    'python': ['import_statement', 'import_from_statement'],
    'javascript': ['import_statement'],
    'java': ['import_declaration'],
    'typescript': ['import_statement'],

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


def get_file_hash(content):
    # generate md5 hash of file content
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def extract_functions(tree, code_bytes, node_types):
    functions = []

    def walk(node):
        if node.type in node_types:
            name_node = node.child_by_field_name('name')
            if name_node:
                functions.append({
                    'name': code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8'),
                    'line': node.start_point[0] + 1
                })
            elif node.parent and node.parent.type == 'variable_declarator':
                name_node = node.parent.child_by_field_name('name')
                if name_node:
                    functions.append({
                        'name': code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8'),
                        'line': node.start_point[0] + 1
                    })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return functions

def extract_classes(tree, code_bytes,node_types):
    # loop tree → find class_definition nodes → extract name and line number
    classes = []

    def walk(node):
        if node.type in node_types:
            name_node = node.child_by_field_name('name')
            if name_node:
                classes.append({
                    'name': code_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8'),
                    'line': node.start_point[0] + 1
                })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return classes

def extract_imports(tree, code_bytes,node_types):
    # loop tree → find import nodes → extract module name and line number
    imports = []

    def walk(node):
        if node.type in node_types:
            imports.append({
                'name': code_bytes[node.start_byte:node.end_byte].decode('utf-8').strip(),
                'line': node.start_point[0] + 1
            })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return imports


def summarize_file(filepath, content, language):
    # call Groq → get 3 line summary → store instead of raw content
    try:
        from groq import Groq
        from dotenv import load_dotenv
        load_dotenv()

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        prompt = f"""Summarize this {language} file in exactly 3 sentences.
Focus on: what it does, what functions matter, what it connects to.
File: {filepath}
Code:
{content[:3000]}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not summarize: {str(e)}"


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
    classes = []
    imports = []

    # if language supported by tree-sitter → parse and extract functions
    if language in LANGUAGE_MAP:
        parser = Parser(LANGUAGE_MAP[language])
        tree = parser.parse(code_bytes)
        functions = extract_functions(tree, code_bytes, FUNCTION_NODES.get(language, []))
        classes = extract_classes(tree, code_bytes,CLASS_NODES.get(language,[]))
        imports = extract_imports(tree, code_bytes, IMPORT_NODES.get(language, []))


    return {
        'filepath': filepath,
        'language': language,
        'imports': imports,
        'functions': functions,
        'classes': classes,
        'summary': summarize_file(filepath, content, language),
        'hash': get_file_hash(content)
    }
