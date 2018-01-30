

import requests

from conf import settings

def get_url():
    return settings.SERVER


def get_auth():
    return (settings.user, settings.password)


def get_verify():
    return settings.SSL_VERIFY
