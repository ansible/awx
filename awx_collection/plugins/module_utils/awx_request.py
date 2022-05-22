import requests

def get_awx_resources(uri, previousPageResults, awx_auth):
    response = requests.get(url=awx_auth['host']+uri, auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['verify_ssl'])
    results = previousPageResults + response['results']
    if response['next']:
        return results
    return get_awx_resources(awx_auth, response['next'], previousPageResults)