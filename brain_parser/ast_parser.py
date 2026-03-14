import ast
import os

def parse_file(filepath):
    #hello world
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        source=f.read()
    try:
       tree=ast.parse(source)
       return tree
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return None

def extract_imports(tree):
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "name": alias.name,
                    "type": "direct"
                })
        if isinstance(node, ast.ImportFrom):
            imports.append({
                "module": node.module or "unknown",
                "type": "from"
            })
    return imports

def extract_classes_and_functions(tree):
    classes = []
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno
            })
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "args": [arg.id if hasattr(arg, 'id') else arg.arg
                         for arg in node.args.args],
                "line": node.lineno
            })
    return {"classes": classes, "functions": functions}


def analyze_file(filepath):
    tree = parse_file(filepath)
    if tree is None:
        return None

    return {
        "file":filepath ,
        "imports":extract_imports(tree),
        "classes_and_functions":extract_classes_and_functions(tree)
    }
if __name__ == "__main__":
    result = analyze_file("utils.py")
    print(result)