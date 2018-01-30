

import requests

from conf import settings


def get_url():
    return settings.SERVER


def get_auth():
    return (settings.user, settings.password)


def get_verify():
    return settings.SSL_VERIFY


def unpaginate(server, url, verify, auth, filter_data):
    results = []
    while url is not None:
        url = "{0}{1}".format(server, url)
        data = requests.get(url, verify=verify, auth=auth, params=filter_data).json()
        results.extend(data.get('results', []))
        url = data.get('next', None)
    return results
