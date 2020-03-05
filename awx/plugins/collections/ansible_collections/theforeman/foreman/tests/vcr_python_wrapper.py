#!/usr/bin/env python

import os
import sys
import vcr
import json


# We need our own json level2 matcher, because, python2 and python3 do not save
# dictionaries in the same order
def body_json_l2_matcher(r1, r2):
    if r1.headers.get('content-type') == r2.headers.get('content-type') == 'application/json':
        if r1.body is None or r2.body is None:
            return r1.body == r2.body
        body1 = json.loads(r1.body.decode('utf8'))
        body2 = json.loads(r2.body.decode('utf8'))
        if 'common_parameter' in body1 and 'common_parameter' in body2:
            if body1['common_parameter'].get('parameter_type') == body2['common_parameter'].get('parameter_type') in ['hash', 'json', 'yaml']:
                body1['common_parameter']['value'] = json.loads(body1['common_parameter'].get('value'))
                body2['common_parameter']['value'] = json.loads(body2['common_parameter'].get('value'))
        return body1 == body2
    elif (r1.headers.get('content-type') == r2.headers.get('content-type')
            and r1.headers.get('content-type') in ['multipart/form-data', 'application/x-www-form-urlencoded']):
        if r1.body is None or r2.body is None:
            return r1.body == r2.body
        body1 = sorted(r1.body.replace(b'~', b'%7E').split(b'&'))
        body2 = sorted(r2.body.replace(b'~', b'%7E').split(b'&'))
        if len(body1) != len(body2):
            return False
        for i, v in enumerate(body1):
            if body1[i] != body2[i]:
                return False
        return True
    else:
        return r1.body == r2.body


def snapshot_query_matcher(r1, r2):
    if r1.path == '/api/hosts' and r2.path == '/api/hosts':
        return [q for q in r1.query if q[0] != 'search'] == [q for q in r2.query if q[0] != 'search']
    return r1.query == r2.query


def query_matcher_ignore_proxy(r1, r2):
    if r1.path == '/api/smart_proxies' and r2.path == '/api/smart_proxies':
        return [q for q in r1.query if q[0] != 'search'] == [q for q in r2.query if q[0] != 'search']
    return r1.query == r2.query


def katello_manifest_body_matcher(r1, r2):
    if r1.path.endswith('/subscriptions/upload') and r2.path.endswith('/subscriptions/upload'):
        if r1.headers.get('content-type').startswith('multipart/form-data') and r2.headers.get('content-type').startswith('multipart/form-data'):
            r1_copy = vcr.request.Request(r1.method, r1.uri, r1.body, r1.headers)
            r2_copy = vcr.request.Request(r2.method, r2.uri, r2.body, r2.headers)
            # the body is a huge binary blob, which seems to differ on every run, so we just ignore it
            body1 = body2 = {}
            r1_copy.body = json.dumps(body1)
            r2_copy.body = json.dumps(body2)
            return body_json_l2_matcher(r1_copy, r2_copy)
    return body_json_l2_matcher(r1, r2)


def host_body_matcher(r1, r2):
    if r1.headers.get('content-type') == r2.headers.get('content-type') == 'application/json':
        if r1.path == r2.path == '/api/v2/hostgroups':
            r1_copy = vcr.request.Request(r1.method, r1.uri, r1.body, r1.headers)
            r2_copy = vcr.request.Request(r2.method, r2.uri, r2.body, r2.headers)
            body1 = json.loads(r1_copy.body.decode('utf8'))
            body2 = json.loads(r2_copy.body.decode('utf8'))
            body1['search'] = 'name="test_group"'
            body2['search'] = 'name="test_group"'
            r1_copy.body = json.dumps(body1)
            r2_copy.body = json.dumps(body2)
            return body_json_l2_matcher(r1_copy, r2_copy)
    return body_json_l2_matcher(r1, r2)


def filter_apipie_checksum(response):
    # headers should be case insensitive, but for some reason they weren't for me
    response['headers'].pop('apipie-checksum', None)
    response['headers'].pop('Apipie-Checksum', None)
    return response


VCR_PARAMS_FILE = os.environ.get('FAM_TEST_VCR_PARAMS_FILE')

# Remove the name of the wrapper from argv
# (to make it look like the module had been called directly)
sys.argv.pop(0)

if VCR_PARAMS_FILE is None:
    # Run the program as if nothing had happened
    with open(sys.argv[0]) as f:
        code = compile(f.read(), sys.argv[0], 'exec')
        exec(code)
else:
    # Run the program wrapped within vcr cassette recorder
    # Load recording parameters from file
    with open(VCR_PARAMS_FILE, 'r') as params_file:
        test_params = json.load(params_file)
    cassette_file = 'fixtures/{}-{}.yml'.format(test_params['test_name'], test_params['serial'])
    # Increase serial and dump back to file
    test_params['serial'] += 1
    with open(VCR_PARAMS_FILE, 'w') as params_file:
        json.dump(test_params, params_file)

    # Call the original python script with vcr-cassette in place
    fam_vcr = vcr.VCR()

    if test_params['test_name'] in ['domain', 'hostgroup', 'katello_hostgroup', 'luna_hostgroup', 'realm']:
        fam_vcr.register_matcher('query_ignore_proxy', query_matcher_ignore_proxy)
        query_matcher = 'query_ignore_proxy'
    elif test_params['test_name'] == 'snapshot':
        fam_vcr.register_matcher('snapshot_query', snapshot_query_matcher)
        query_matcher = 'snapshot_query'
    else:
        query_matcher = 'query'

    fam_vcr.register_matcher('body_json_l2', body_json_l2_matcher)

    body_matcher = 'body_json_l2'
    if test_params['test_name'] == 'host':
        fam_vcr.register_matcher('host_body', host_body_matcher)
        body_matcher = 'host_body'
    elif test_params['test_name'] == 'katello_manifest':
        fam_vcr.register_matcher('katello_manifest_body', katello_manifest_body_matcher)
        body_matcher = 'katello_manifest_body'

    with fam_vcr.use_cassette(cassette_file,
                              record_mode=test_params['record_mode'],
                              match_on=['method', 'path', query_matcher, body_matcher],
                              filter_headers=['Authorization'],
                              before_record_response=filter_apipie_checksum,
                              decode_compressed_response=True,
                              ):
        with open(sys.argv[0]) as f:
            code = compile(f.read(), sys.argv[0], 'exec')
            exec(code)
