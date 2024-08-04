from analysis2 import AbsState, L


a = AbsState()
print(a)
for v in {'a','b','c','d'}:
    a.add_z_var(v)

print(a)


