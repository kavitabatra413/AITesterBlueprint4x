class Dog:
    # A
    name = None
    breed = None
    height = None
    weight = None
    # B
    def bark(self):
        print("Barking") #Barking
        # print(name)
        print(self.name)#None

    def talk(self):
        print("Talking") #Talking


chow = Dog()

# Dog() - Object
# chow -> Object Ref

chow.bark()
chow.talk()