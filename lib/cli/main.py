import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import json

# this is temporary
username = os.getenv("ACOM_USER","admin")
password = os.getenv("ACOM_PASS","admin")
print "USER=%s" % username
server   = os.getenv("ACOM_SERVER","http://127.0.0.1:8000")

# TODO: error handling/output/etc
# TODO: format into actual command line

PARAMS = {
   'format'           : 'json',
}
HEADERS = {
   'Content-Type' : 'application/json'
}
AUTH = HTTPBasicAuth(username, password)

def get(url_seg, expect=200):
   resp = requests.get("%s/api/v1/%s" % (server, url_seg), auth=AUTH)
   if resp.status_code != expect:
       assert "GET: Expecting %s got %s: %s" % (expect, resp.status_code, resp.text)
   return resp

def post(url_seg, data, expect=201):
   resp = requests.post("%s/api/v1/%s" % (server, url_seg), auth=AUTH, data=data, headers=HEADERS)
   if resp.status_code != expect:
       assert "POST: Expecting %s got %s: %s" % (expect, resp.status_code, resp.text)
   return resp

class Collection(object):

   def __init__(self):

       self.response = get(self.base_url())

       print self.response.text
       print self.response.status_code
       # TODO: error handling on non-200
       self.data     = json.loads(self.response.text)
       self.meta     = self.data['meta']
       self.objects  = self.data['objects']
       self.meta     = self.data['meta']
       self.objects  = self.data['objects']
        
   def base_url(self):
       return exceptions.NotImplementedError()

   def add(self, data):
       json_data = json.dumps(data)
       response = post(self.base_url(), data=json_data)
       return Entry(data)

   def __iter__(self):
       for x in self.objects:
           yield Entry(x)

class Entry(object):

   def __init__(self, data):
       self.data = data
       self.resource_uri = data.get('resource_uri', None)

   def __repr__(self):
       return repr(self.data)

class Organizations(Collection):

   def base_url(self):
       return "organizations/"

#(Epdb) got.text
#u'{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 1}, "objects": [{"active": true, "creation_date": "2013-03-15", "description": "testorg!", "id": 1, "name": "testorg", "resource_uri": "/api/v1/organizations/1/"}]}'
#

try:
    print "---"
    orgs = Organizations()
    for x in orgs:
       print x
    print "---"
    orgs.add(dict(description="new org?", name="new org"))
    print "---"
    
    print "---"
    orgs = Organizations()
    for x in orgs:
       print x
    

except requests.exceptions.ConnectionError:
    print "connect failed"
    sys.exit(1)

