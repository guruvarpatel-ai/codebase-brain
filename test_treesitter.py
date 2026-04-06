import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

code = b"def hello(): pass"

tree = parser.parse(code)
print(tree.root_node)
print(tree.root_node.children)


def extract_functions(tree, code):
    functions = []

    def walk(node):
        if node.type == 'function_definition':
            name_node = node.child_by_field_name('name')
            if name_node:
                functions.append({
                    'name': code[name_node.start_byte:name_node.end_byte].decode('utf-8'),
                    'line': node.start_point[0] + 1
                })
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return functions


code = b"def hello(): pass\ndef world(): pass"
tree = parser.parse(code)
print(extract_functions(tree, code))