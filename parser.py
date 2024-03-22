
def obtain_function(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    find = False
    groups = [[]]
    for line in lines:
        if line.startswith('#'):
            continue
        if '@guppy' in line:
            if find:
                groups.append([])
            else:
                find = True
        else:
            if find:
                groups[-1].append(line)

    return groups


