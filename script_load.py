# importing the requests library
import requests

# api-endpoint
BASE_URL = "http://localhost:5000"

# sending get request and saving the response as response object
r = requests.get(url = BASE_URL)

# printing the output
print(r)