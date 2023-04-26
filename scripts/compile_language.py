from tree_sitter import Language

Language.build_library(
  # Store the library
  'postman_auto_collection/language_libs.so',

  # Include one or more languages
  ['tree-sitter-python']
)
