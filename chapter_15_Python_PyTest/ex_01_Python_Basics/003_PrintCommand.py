print("Hello", "World")
print("Hello", "World", "TheTestingAcademy", sep="*")
print("Hello", "World", "TheTestingAcademy", sep="__")


print("*", "*", sep="-", end="\t")
print("*", "*", sep="_")

# Hello World
# Hello*World*TheTestingAcademy
# Hello__World__TheTestingAcademy
# *-*    *_*
# Explanation of the last two print statements:
# sep="-" joins the two * values with a hyphen: *-*
# end="\t" adds a tab instead of a new line.
# The next print() continues on the same line.
# sep="_" joins the two * values with an underscore: *_*
