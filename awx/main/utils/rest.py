import urllib2
import json

__all__ = ['fetch_dynamic_options']


def fetch_dynamic_options(url):
    try:
        return "\n".join(json.loads(urllib2.urlopen(url).read()))
    except Exception as err:
        return "Fetch error: {0}".format(err)
