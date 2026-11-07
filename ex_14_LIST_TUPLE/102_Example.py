cities = ("London", "Paris", "Los Angeles", "Tokyo")
print(len(cities))

print("Paris" in cities) #True
print("New Delhi" in cities) #False


ENV_API_URLS = tuple(["abc.com/get", "xyz.com/post", "qwe.com/put"])
print(ENV_API_URLS) #('abc.com/get', 'xyz.com/post', 'qwe.com/put')



colors = ("red", "green", "blue")
for c in colors:
    print(c)

# 4
#True
#False
#('abc.com/get', 'xyz.com/post', 'qwe.com/put')
#red
#green
#blue
