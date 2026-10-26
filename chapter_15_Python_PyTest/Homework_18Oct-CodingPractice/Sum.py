# methods.py

num1 = float(input("first"))
num2 = float(input("second"))
num3 = float(input("third"))

# sum
print("Sum =", num1 + num2 + num3)

# Subtract
print("Subtract =", num1 - num2 - num3)

# Multiply
print("Multiply =", num1 * num2 * num3)

# Divide
if num2 != 0 and num3 != 0:
    print("Divide =", num1 / num2 / num3)
else:
    print("No division as divisor is zero.")