import time
# https://www.epochconverter.com/
def time_decorator(func):
    def wrapper():
        start_time = time.time()
        print(start_time)
        func()
        end_time = time.time()
        print(end_time)
        print("Total Time Take by Func -> ", end_time - start_time)
    return wrapper

def print_logs(func):
    def wrapper():
        print("Start the logs")
        func()
        print("End of the log")
    return wrapper


@time_decorator
@print_logs
def test_ui_1():
    print("Add a function, time taken by this function 1")
    time.sleep(2)


def test_ui_2():
    print("Add a function, time taken by this function 2")
    time.sleep(5)

print(" -----  ")

#with decor
test_ui_1()

print(" -----  ")
# without the decor
test_ui_2()

# 1793623507.0014544
# Start the logs
# Add a function, time taken by this function 1
# End of the log
# 1793623509.0044713
# Total Time Take by Func ->  2.003016948699951
 -----  
# Add a function, time taken by this function 2