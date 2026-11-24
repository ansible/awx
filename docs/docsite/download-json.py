import requests

downloads = [
    {"url": "https://awx-public-ci-files.s3.amazonaws.com/community-docs/swagger.json", "path": "./docs/docsite/rst/rest_api/_swagger/swagger.json"},
    {"url": "https://s3.amazonaws.com/awx-public-ci-files/awx/devel/schema.json", "path": "./docs/docsite/rst/open_api/schema.json"},
]

for item in downloads:
    url = item["url"]
    filepath = item["path"]

    response = requests.get(url)

    if response.status_code == 200:
        with open(filepath, 'wb') as file:
            file.write(response.content)
        print(f"JSON file downloaded to {filepath}")
    else:
        print(f"Request failed with status code: {response.status_code}")
