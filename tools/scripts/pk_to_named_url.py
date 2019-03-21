#!/usr/bin/env python
import argparse
import urllib.parse

import requests


NAMED_URL_RES_DILIMITER = "--"
NAMED_URL_RES_INNER_DILIMITER = "-"
NAMED_URL_RES_DILIMITER_ENCODE = "%2D"
URL_PATH_RESERVED_CHARSET = {}
for c in ';/?:@=&[]':
    URL_PATH_RESERVED_CHARSET[c] = urllib.parse.quote(c, safe='')


def _get_named_url_graph(url, auth):
    """Get the graph data structure Tower used to manage all named URLs.

    Args:
        url: String representing the URL of tower configuration endpoint where
            to fetch graph information.
        auth: Tuple of username + password to authenticate connection to Tower.

    Return:
        A dict of graph nodes that in ensembly represent the graph structure. Each
        node is represented as a dict of 'fields' and 'adj_list'.

    Raises:
        N/A
    """
    r = requests.get(url, auth=auth, verify=False)
    ret = r.json()['NAMED_URL_GRAPH_NODES']
    return ret


def _encode_uri(text):
    """Properly encode input text to make it satisfy named URL convention.

    Args:
        text: the original string to be encoded.

    Return:
        The encoded string

    Raises:
        N/A
    """
    for c in URL_PATH_RESERVED_CHARSET:
        if c in text:
            text = text.replace(c, URL_PATH_RESERVED_CHARSET[c])
    text = text.replace(NAMED_URL_RES_INNER_DILIMITER,
                        '[%s]' % NAMED_URL_RES_INNER_DILIMITER)
    return text


def _generate_identifier_component(response, fields):
    """Generate an individual component of named URL identifier.

    Args:
        response: JSON containing the details of a particular resource object.
        fields: name of resource object fields needed to generate a named URL
            identifier component.

    Return:
        A string representing generated identifier component.

    Raises:
        N/A
    """
    ret = []
    for field_name in fields:
        ret.append(_encode_uri(response[field_name]))
    return NAMED_URL_RES_INNER_DILIMITER.join(ret)


def _get_named_url_identifier(url, named_url_graph, resource, tower_host, auth, ret):
    """DFS the named URL graph structure to generate identifier for a resource object.

    Args:
        url: A string used to access a particular resource object to generate identifier
            component from.
        named_url_graph: The graph structure used to DFS against.
        resource: Key name of the current graph node.
        tower_host: String representing the host name of Tower backend.
        auth: Tuple of username + password to authenticate connection to Tower.
        ret: list of strings storing components that would later be joined into
            the final named URL identifier.

    Return:
        None. Note the actual outcome is stored in argument ret due to the recursive
        nature of this function.

    Raises:
    """
    r = requests.get(url, auth=auth, verify=False).json()
    ret.append(_generate_identifier_component(r, named_url_graph[resource]['fields']))
    for next_ in named_url_graph[resource]['adj_list']:
        next_fk, next_res = tuple(next_)
        if next_fk in r['related']:
            _get_named_url_identifier(tower_host.strip('/') + r['related'][next_fk],
                                      named_url_graph, next_res, tower_host, auth, ret)
        else:
            ret.append('')


def main(username=None, password=None, tower_host=None, resource=None, pk=None):
    """Main function for generating and printing named URL of a resource object given its pk.

    Args:
        username: String representing the username needed to authenticating Tower.
        password: String representing the password needed to authenticating Tower.
        tower_host: String representing the host name of Tower backend.
        resource: REST API name of a specific resource, e.g. name for resource inventory
            is 'inventories'.
        pk: Primary key of the resource object whose named URL will be derived.

    Returns:
        None

    Raises:
        N/A
    """
    start_url = '%s/api/v2/%s/%s/' % (tower_host.strip('/'), resource.strip('/'), pk)
    conf_url = '%s/api/v2/settings/named-url/' % tower_host.strip('/')
    auth = (username, password)
    named_url_graph = _get_named_url_graph(conf_url, auth)
    named_url_identifier = []
    _get_named_url_identifier(start_url, named_url_graph, resource,
                              tower_host, auth, named_url_identifier)
    print('%s/api/v2/%s/%s/' % (tower_host.strip('/'), resource.strip('/'),
                                NAMED_URL_RES_DILIMITER.join(named_url_identifier)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', type=str, required=True,
                        help='Name of the Tower user for making requests',
                        dest='username', metavar='STR')
    parser.add_argument('--password', type=str, required=True,
                        help='Password of the Tower user for making requests',
                        dest='password', metavar='STR')
    parser.add_argument('--tower-host', type=str, required=True,
                        help='Tower host name, like "http://127.0.0.1"',
                        dest='tower_host', metavar='STR')
    parser.add_argument('--resource', type=str, required=True,
                        help='Name of the resource in REST endpoints',
                        dest='resource', metavar='STR')
    parser.add_argument('--pk', type=int, required=True,
                        help='Primary key of resource object whose named URL will be derived',
                        dest='pk', metavar='INT')
    main(**vars(parser.parse_args()))
