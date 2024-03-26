# Lista di set di esempio
list_of_sets = [{1, 2}, {3, 4}, {5, 6, 7}]

# Valori specifici da cercare
var1 = 5
var2 = 7

# Cerca i set che contengono i valori specifici
set_v1 = [s for s in list_of_sets if var1 in s]
set_v2 = [s for s in list_of_sets if var2 in s]




if set_v1 != set_v2:
    exit('Partition ill-formed')


list_of_sets.remove(set_v1[0])
set_v1[0].discard(var2)
list_of_sets.append(set_v1[0])
list_of_sets.append({var2})

print(list_of_sets)
