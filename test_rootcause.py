from brain_parser.root_cause import find_root_cause

error = 'File "brain_parser/graph_builder.py", line 45, in build_graph'

print(find_root_cause(error))