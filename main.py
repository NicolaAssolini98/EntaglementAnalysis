from analysis2 import *
from cfg_build import *
from lark import Lark
from lark.indenter import PythonIndenter


kwargs = dict(postlex=PythonIndenter())
parser = Lark.open("lark/grammar_l1.lark", rel_to=__file__, parser="lalr", **kwargs)

text = '''
[a,b,c]
h(a)
cx(a,c)
h(a)
cx(c,b)
# t(b)
# cx(c,a)
if b:
    skip
'''


'''
[c,a,b] #,d,e]
skip
while c:
    h(a)
    # skip
# t(a)
cx(a,c)
'''


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
