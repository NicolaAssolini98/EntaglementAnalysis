import os

from analysis2 import *
from cfg_build import *
from lark import Lark
from lark.indenter import PythonIndenter


kwargs = dict(postlex=PythonIndenter())
parser = Lark.open("lark/grammar_l1.lark", rel_to=__file__, parser="lalr", **kwargs)


test_folder_path = 'txt_files'
test_files = os.listdir(test_folder_path)

# Iterate through each file in the folder
for test_file in test_files:
    file_path = os.path.join(test_folder_path, test_file)
    with open(file_path, 'r') as file:
        text = file.read()
        print('---------\ncode:\n')
        print(text)
        t = parser.parse(text)
        # print(t)
        # print(t.pretty())
        decl_vars, cfg = init_cfg(t)
        # print(decl_vars)
        # print(cfg)
        print_cfg(cfg)
        abs_states = entanglement_analysis(decl_vars, cfg)
        for n in abs_states.keys():
            print(f'{n}: {abs_states[n]}')
        print('---------\n')
