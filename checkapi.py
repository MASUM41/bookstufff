import requests

# 1. Define the API endpoint
url = "http://127.0.0.1:8000/books"

# 2. Make the GET request
response = requests.get(url)

# 3. Check if it was successful (Status Code 200)
if response.status_code == 200:
    data = response.json()  # Convert JSON response to a Python dictionary
    print(f"Successfully fetched {data['count']} books.")
    
    # Print the first book title as an example
    if data['data']:
        print(f"First book: {data['data'][0]['title']}")
else:
    print(f"Error: {response.status_code}")