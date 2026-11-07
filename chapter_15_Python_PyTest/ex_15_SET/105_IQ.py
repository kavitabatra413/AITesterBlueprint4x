t = ("TheTestingAcademy", "for", "TheTestingAcademy")
print(t) #('TheTestingAcademy', 'for', 'TheTestingAcademy')
print(set(t)) #{'for', 'TheTestingAcademy'}

empty = set() #set is a built-in class used to create a set.
print(type(empty)) #<class 'set'>


mixed = {1, "QA", True, 3.5}
for item in mixed:
    print(item)

#1
#3.5
#QA

mixed.add(10)
print(mixed) #{1, 10, 3.5, 'QA'}
mixed.remove(10)
print(mixed) #{1, 3.5, 'QA'}


# 1 and True are considered equal in Python.
#Therefore, the set will contain only one of them because sets do not allow duplicate elements.