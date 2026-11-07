squares = [1, 4, 9, 16, 25]

print(squares)#[1, 4, 9, 16, 25]
print(squares.pop()) # Remove and return item at index (default last) ie 25

print(squares)
print(squares.pop(1))
print(squares)

squares.clear()
print(squares)

#[1, 4, 9, 16, 25]
#25
#[1, 4, 9, 16]
#4
#[1, 9, 16]
#[]