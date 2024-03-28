def unique_elements_from_sets(list_of_sets):
    # Initialize an empty set to store unique elements
    unique_elements = set()

    # Iterate through each set in the list
    for s in list_of_sets:
        # Add the elements of the current set to the set of unique elements
        unique_elements.update(s)

    # Convert the set of unique elements to a list and return it
    return unique_elements

# Example usage
list_of_sets = [{1, 2, 3}, {3, 4, 5}, {5, 6, 7}]
unique_elements = unique_elements_from_sets(list_of_sets)
print("List of unique elements:", unique_elements)


# Esempio di utilizzo
list_of_sets = [{1, 2, 3}, {3, 4, 5}, {5, 6, 7}]
unique_elements = unique_elements_from_sets(list_of_sets)
print("Lista degli elementi unici:", unique_elements)
for u in unique_elements:
    print(u)
