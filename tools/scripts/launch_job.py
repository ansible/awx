#!/usr/bin/env python

import datetime
import getpass
import json
import urllib2

REST_API_URL = "http://awx.example.com/api/v1/"
REST_API_USER = "admin"
REST_API_PASS = "password"
JOB_TEMPLATE_ID = 1

# Setup urllib2 for basic password authentication.
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, REST_API_URL, REST_API_USER, REST_API_PASS)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)

# Read the job template.
JOB_TEMPLATE_URL="%sjob_templates/%d/" % (REST_API_URL, JOB_TEMPLATE_ID)
response = urllib2.urlopen(JOB_TEMPLATE_URL)
data = json.loads(response.read())

# Update data if needed for the new job.
data.pop('id')
data.update({
    'name': 'my new job started at %s' % str(datetime.datetime.now()),
    'verbosity': 3,
})

# Create a new job based on the template and data.
JOB_TEMPLATE_JOBS_URL="%sjobs/" % JOB_TEMPLATE_URL
request = urllib2.Request(JOB_TEMPLATE_JOBS_URL, json.dumps(data),
                          {'Content-type': 'application/json'})
response = urllib2.urlopen(request)
data = json.loads(response.read())

# Get the job ID and check for passwords needed to start the job.
JOB_ID = data['id']
JOB_START_URL = '%sjobs/%d/start/' % (REST_API_URL, JOB_ID)
response = urllib2.urlopen(JOB_START_URL)
data = json.loads(response.read())

# Prompt for any passwords needed.
start_data = {}
for password in data.get('passwords_needed_to_start', []):
    value = getpass.getpass('%s: ' % password)
    start_data[password] = value

# Make POST request to start the job.
request = urllib2.Request(JOB_START_URL, json.dumps(start_data),
                          {'Content-type': 'application/json'})
response = urllib2.urlopen(request)
