from collections import defaultdict


def reverse_defaultdict(default_dict):
    # Initialize an empty dictionary to store the reversed pairs
    reversed_dict = {}

    # Iterate over the items in the defaultdict
    for key, value_set in default_dict.items():
        print(value_set)
        # Iterate over each value in the set
        for value in value_set:
            # Add the value as the key and the original key as the value in the new dict
            reversed_dict[value] = key

    return reversed_dict


# Example usage:
default_dict = defaultdict(set, {1: {'a', 'b'}, 2: {'c', 'd'}})
reversed_dict = reverse_defaultdict(default_dict)
print(reversed_dict)
