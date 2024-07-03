import requests

url = "https://awx-public-ci-files.s3.amazonaws.com/community-docs/swagger.json"
swagger_json = "./docs/docsite/rst/rest_api/_swagger/swagger.json"

response = requests.get(url)

if response.status_code == 200:
    with open(swagger_json, 'wb') as file:
        file.write(response.content)
    print(f"JSON file downloaded to {swagger_json}")
else:
    print(f"Request failed with status code: {response.status_code}")
