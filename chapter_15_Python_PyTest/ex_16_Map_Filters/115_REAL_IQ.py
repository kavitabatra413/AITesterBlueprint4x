names = ["QA", "", "Automation", "", "Tester"]

def non_empty(x):
    if x != "":
        return True
    return None


non_empty = list(filter(non_empty, names))  # removes empty strings
print(non_empty) #['QA', 'Automation', 'Tester']


#In Python, filter() works based on truthy and falsy values.
# True → Keep the element.
# False → Remove the element.
# None → Remove the element.