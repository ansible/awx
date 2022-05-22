import requests

def get_awx_resources(uri, previousPageData, awx_auth):
    resourceUri = uri.replace('/api/v2', '')
    response = requests.get(url=awx_auth['awx_host']+resourceUri, auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['verify_ssl'])
    results = previousPageData + response['results']
    if 'next' not in response:
        return results
    return get_awx_resources(awx_auth, response['next'], previousPageData)