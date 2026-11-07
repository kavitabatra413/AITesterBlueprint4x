def add_security(func):
    def wrapper():
        print("1.Before the function is called.")
        print("2.Add Helmet, Dashcash, gloves, knee guards, License")
        func()
        print("3.After the function is called.")
        print("4.Secure Driving, Leave all the items")

    return wrapper


@add_security
def drive_ola_scooter():
    print("I am driving ola scooter")


drive_ola_scooter()

#1. Before the function is called.
#2. Add Helmet, Dashcash, Gloves, Knee Guards, License.
#I am driving an Ola scooter.
#3. After the function is called.
#4. Secure Driving, Leave all the items.
