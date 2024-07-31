from analysis2 import *

a1 = AbsDomain([({'a', 'b', 'c'}, 0), ({'d'}, 0)], {0: L.X})
a2 = AbsDomain([({'a', 'b'}, 0), ({'e'}, 1)], {0: L.Y, 1: L.S})

r = lub_abs_dom(a1, a2)
print(r)
