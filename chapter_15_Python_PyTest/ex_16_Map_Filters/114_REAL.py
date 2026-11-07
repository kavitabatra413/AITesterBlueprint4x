test_results = ["PASS", "FAIL", "PASS", "SKIP", "FAIL"]

pass_give = list(filter(lambda x: x == "PASS", test_results))
print(pass_give) #['PASS', 'PASS']

# no need to write a function, we can use lambda function to filter the list