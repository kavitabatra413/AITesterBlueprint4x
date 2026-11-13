keys = ["name", "role", "experience", "abc"]
values = ["Aman", "SDET", 3, 67,90]
# values = ["Aman", "SDET"]

my_dict = dict(zip(keys, values))
print(my_dict)#{'name': 'Aman', 'role': 'SDET', 'experience': 3, 'abc': 67}

dict1 = {"a": 1, "b": 2}
dict2 = {"b": 2, "a": 1}

print(dict1 == dict2) # True