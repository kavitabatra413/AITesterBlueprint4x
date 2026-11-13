my_dict = {
    "name": "Aman",
    "age": 34,
    "role": "SDET",
    "exp": 3
}

print(my_dict) #{'name': 'Aman', 'age': 34, 'role': 'SDET', 'exp': 3}
print(my_dict["age"]) #34
print(my_dict["role"]) #SDET

my_dict["role"] = "Manual Tester"
print(my_dict)
#{'name': 'Aman', 'age': 34, 'role': 'Manual Tester', 'exp': 3}


del my_dict["age"]
print(my_dict)#{'name': 'Aman', 'role': 'Manual Tester', 'exp': 3}


for key, value in my_dict.items():
    print(key, value)
    # name Aman
    # role Manual Tester
    # exp 3

print("age" in my_dict) #False because the age key was deleted.
print("role" in my_dict) #True because the role key is present in the dictionary.

#direct run by arrow function