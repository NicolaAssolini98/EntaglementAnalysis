from analysis2 import *

b = AbsState()
for v in {'a','b'}:
    b.add_z_var(str(v))
a = AbsState()

c = lub_abs_dom(b,a)
print(c)
d = lub_abs_dom(a,b)
print(d)




