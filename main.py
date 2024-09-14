import os

from analysis2 import *
from cfg_build import *
from lark import Lark
from lark.indenter import PythonIndenter


kwargs = dict(postlex=PythonIndenter())
parser = Lark.open("lark/grammar_l1.lark", rel_to=__file__, parser="lalr", **kwargs)


test_folder_path = 'test'
test_files = os.listdir(test_folder_path)

"""
Iterate through each file in the folder
"""
with open('result.txt', 'w') as result_file:
    for test_file in test_files:
        file_path = os.path.join(test_folder_path, test_file)
        with open(file_path, 'r') as file:
            text = file.read()
            print(test_file)
            result_file.write(f"Analysis of {test_file}:\n")
            print('---------\ncode:\n')
            result_file.write('--------\ncode:\n')
            print(text)
            result_file.write(f'{text}\n--------\nResults:\n')
            t = parser.parse(text)
            """
            uncomment if you want to print the AST
            """
            # print(t)
            # print(t.pretty())

            decl_vars, cfg = cfg_from_ast(t)
            print_cfg(cfg, True, test_file, 'cfgs')

            abs_states = entanglement_analysis(decl_vars, cfg)
            for n in abs_states.keys():
                print(f'{n}: {abs_states[n]}')
                result_file.write(f"{n}: {abs_states[n]}\n")
            print('---------\n')
            result_file.write('§§§§§§§§§§§§\n\n')
