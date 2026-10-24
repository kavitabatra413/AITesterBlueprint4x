# code for GradeCalculator.py

marks = float(input("Enter marks"))
if marks < 0 or marks > 100:
    print("Invalid marks")
elif marks >= 90:
    print("Grade A")
elif marks >= 80:
    print("Grade B")
elif marks >= 70:
    print("Grade C")
elif marks >= 60:
    print("Grade D")
else:
    print("Grade: F")

#Open terminal
#C:\Users\Kavita Batra\Documents\AITesterBlueprint4x\chapter_15_Python_PyTest\Homework_18Oct-CodingPractice>python GradeCalculator.py
#Enter marks60
#Grade D