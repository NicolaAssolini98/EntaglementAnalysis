from analysis2 import *
from cfg_build import *
from lark import Lark
from lark.indenter import PythonIndenter


kwargs = dict(postlex=PythonIndenter())
parser = Lark.open("lark/grammar_l1.lark", rel_to=__file__, parser="lalr", **kwargs)

text = '''
[a]#b,c,d,e]
# cx(a,b)
# skip
# h(d)
# t(e)
# if a:
#     t(b)
# else:
#     h(b)
while c:
    h(c)
    t(c)
'''


t = parser.parse(text)
print(t)
print(t.pretty())
decl_vars, cfg = init_cfg(t)
print(decl_vars)
print(cfg)
print_cfg(cfg)
