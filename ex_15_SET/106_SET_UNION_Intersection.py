a = {1, 2, 3}
b = {3, 4, 5}

print(a | b) #{1, 2, 3, 4, 5}
print(a.union(b)) #{1, 2, 3, 4, 5}

print(a & b) # {3}
print(a.intersection(b)) # {3}

print(a - b) # {1, 2}
print(b - a)  # {4, 5}