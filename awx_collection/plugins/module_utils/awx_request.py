#!/usr/bin/python
import requests

def get_awx_resources(uri, previousPageResults, awx_auth):
    response = requests.get(url='https://'+awx_auth['host']+uri, auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['validate_certs']).json()
    results = previousPageResults + response['results']
    if response['next'] is None:
        return results
    return get_awx_resources(response['next'], previousPageResults, awx_auth)

def get_awx_resource_by_id(resource, id, awx_auth):
    return requests.get(url='https://'+awx_auth['host']+'/api/v2/'+resource+'s/'+str(id)+'/', auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['validate_certs']).json()

def get_awx_resource_by_name(resource, name, awx_auth):
    return requests.get(url='https://'+awx_auth['host']+'/api/v2/'+resource+'s/?name='+name, auth=(awx_auth['username'], awx_auth['password']), verify=awx_auth['validate_certs']).json()['results'][0]
