from analysis2 import *
from lark import Lark
from lark.indenter import PythonIndenter


kwargs = dict(postlex=PythonIndenter())
parser = Lark.open("lark/grammar_l1.lark", rel_to=__file__, parser="lalr", **kwargs)



# t = parser.parse(text)
# print(t)
# print(t.pretty())
