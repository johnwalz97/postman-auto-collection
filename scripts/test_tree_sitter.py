import sys

from tree_sitter import Language, Parser

PY_LANGUAGE = Language('postman_auto_collection/language_libs.so', 'python')

parser = Parser()
parser.set_language(PY_LANGUAGE)

with open("../postman-docs-ai/postman_docs_ai/search.py", "rb") as f:
    tree = parser.parse(f.read())

query = PY_LANGUAGE.query("""
(function_definition
  name: (identifier) @function_name
  body: (block) @function_body
)
""")
captures = query.captures(tree.root_node)

for capture in captures:
    if capture[1] == "function_name":
        func_name = capture[0].text.decode("utf-8")
        print(func_name)
    elif capture[1] == "function_body":
        func_body = capture[0].text.decode("utf-8")
