import math

# built in functions
result = max(3, 4)
print(result)

# 1. They can't return -> non return
# No Return Type and No Parameter / Argument - NRNP

def greet():
    print("Hello")

greet()

# 2. # No Return Type and with Argument/ Param
def greet_by_name(name):
    print("Hello,", name)


greet_by_name("Pramod")

# 3. No Return Type and with Default Argument ( # positional argument)
def say_hello_default_arg(name="Pramod"):
    print("Hello", name.upper())


say_hello_default_arg("Dutta")
say_hello_default_arg()
#Hello DUTTA
#Hello PRAMOD


def multiple_args(name1="A", name2="B"):
    print("Mul -> ", name1, name2)


multiple_args()
multiple_args("Lucky", "Sharma")
multiple_args(name1="Pramod")
multiple_args(name1="Dutta", name2="Amit")
multiple_args(name2="Amit")

# Mul ->  A B
# Mul ->  Lucky Sharma
# Mul ->  Pramod B
# Mul ->  Dutta Amit
# Mul ->  A Amit


# def test(name):
# return name
# print(test("test"))
# test

# 4. Argument + return Type

def sum_of_two(a, b):
    return a + b


result = sum_of_two(4, 56)
print(result)


def sum_of_two_number_with_default(num1=100, num2=200):
    print("I will sum the two numbers!")
    return num1 + num2


result = sum_of_two_number_with_default(num1=34, num2=34)
print(result) #68
result = sum_of_two_number_with_default()
print(result) #300