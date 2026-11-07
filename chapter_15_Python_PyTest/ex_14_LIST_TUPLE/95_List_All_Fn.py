my_list = [1, 2, 3]
# Indexing
print("element at the index 0 - ", my_list[0])
print("element at the index 1 - ", my_list[1])
print("element at the index 2 - ", my_list[2])

my_list.append(4)
print(my_list)#[1, 2, 3, 4]


my_list.append(5)
print(my_list)#[1, 2, 3, 4, 5]


# extend() - Append a new list
my_list.extend([7, 8, 10, 9])
print(my_list)#[1, 2, 3, 4, 5, 7, 8, 10, 9]


# insert()
my_list.insert(1,"Dutta")
print(my_list) #[1, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
print(len(my_list)) #10

my_list.insert(0, 0)
print(my_list)#[0, 1, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]

my_list[1] = "Amit"
print(my_list)#[0, 'Amit', 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]

my_list.remove("Amit")
print(my_list)#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]

my_copy_list = my_list.copy()
print(my_list)#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
print(my_copy_list)#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]

my_copy_list.remove("Dutta")
print(my_list)#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
print(my_copy_list)#[0, 2, 3, 4, 5, 7, 8, 10, 9]

# direct run
#element at the index 0 -  1
#element at the index 1 -  2
#element at the index 2 -  3
#[1, 2, 3, 4]
#[1, 2, 3, 4, 5]
#[1, 2, 3, 4, 5, 7, 8, 10, 9]
#[1, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
#10
#[0, 1, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
#[0, 'Amit', 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
#[0, 'Dutta', 2, 3, 4, 5, 7, 8, 10, 9]
#[0, 2, 3, 4, 5, 7, 8, 10, 9]
