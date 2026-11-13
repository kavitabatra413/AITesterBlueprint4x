student_infor = {
    "name": "Pramod",
    "age": 65,
    "age": 67,
    "address": "KA"
}

print(student_infor)#{'name': 'Pramod', 'age': 67, 'address': 'KA'}

print(student_infor["name"])#Pramod
print(student_infor["age"])#67

print(student_infor["address"])#KA
student_infor["age"] = 100
print(student_infor)#{'name': 'Pramod', 'age': 100, 'address': 'KA'}