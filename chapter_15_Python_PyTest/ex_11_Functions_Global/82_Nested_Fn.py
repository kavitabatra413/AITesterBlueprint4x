def outer_function():
    var1 = 30 # local

    def inner_function():
        var2 = 90
        print(var1)#30

    def inner_function2():
        var1 = 100
        print(var1) #100
        print(var2) #90 #NameError: name 'var2' is not defined. Did you mean: 'var1'?


    inner_function()
    inner_function2()

outer_function()