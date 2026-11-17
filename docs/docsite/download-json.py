import shutil

import requests

downloads = [
    {"url": "https://awx-public-ci-files.s3.amazonaws.com/community-docs/swagger.json", "path": "./docs/docsite/rst/rest_api/_swagger/swagger.json"},
    {"url": "https://s3.amazonaws.com/awx-public-ci-files/awx/devel/openapi.yaml", "path": "./docs/docsite/rst/open_api/openapi.yaml", "fallback": "./openapi.yaml"},
]

for item in downloads:
    url = item["url"]
    filepath = item["path"]
    fallback = item.get("fallback")

    response = requests.get(url)

    if response.status_code == 200:
        with open(filepath, 'wb') as file:
            file.write(response.content)
        print(f"JSON file downloaded to {filepath}")
    elif fallback:
        shutil.copy(fallback, filepath)
        print(f"Download failed ({response.status_code}), using committed spec as fallback")
    else:
        print(f"Request failed with status code: {response.status_code}")
