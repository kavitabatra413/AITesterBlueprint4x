numbers = [1, 2, 3, 4, 5]
def sq(x):
    return x**2

# for n in numbers:
#     print(sq(n))

all_sq = list(map(sq, numbers))
print(all_sq) #[1, 4, 9, 16, 25]

# map() returns a map iterator, not a list.
# list() converts that iterator into a list.
# map() is a built-in function that applies a given function to
# every element of an iterable (such as a list or tuple) and returns the results.