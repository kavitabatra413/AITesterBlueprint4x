class Person:
    # Attributes
    name = None
    id = None
    age = None
    email = None
    height = None
    gender = None
    phone_no = None
    address = None


    # Behaviour ie functions or methods
    def talk(self):  # self - this , self will be first argument in every behaviour.
        print("I can Talk")

    def sleep(self, name):  # Arg with No Return
        print("I am a Method!!")
        print("Sleep", name) #Sleep Geeta

    def sleep2(self, name):  # Arg with Return
        print("I am a Method!!")
        return None

    def walk(self):
        print("I am walking")

    def method_walk_return(self):  # No Arg with Return
        return "I am walking"

def function_outside():
    print("Outside")


geeta = Person()
amit = Person()
navita = Person()

# Calling methods using objects
geeta.talk()

geeta.sleep("Geeta")

geeta.sleep2("Geeta")

geeta.walk()

print(geeta.method_walk_return())

function_outside()

# run direct or python XXX.py