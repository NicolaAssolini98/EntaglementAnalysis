from analysis2 import *


b = AbsState([({'a','c'},0)], {0: L.X})

c = abs_measure(b, 'a')
print(c)




