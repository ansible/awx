import hammock
import os
import requests
import sys
import json

# this is temporary
username = os.getenv("ACOM_USER","admin")
password = os.getenv("ACOM_PASS""admin")
server   = os.getenv("ACOM_SERVER","127.0.0.1:8000")

handle = hammock.Hammock("http://%s/api/v1" % server, auth=(username,password))

class Collection(object):

   def __init__(self, handle):
       self.handle   = handle
       self.response = self.accessor().GET()
       # TODO: error handling on non-200
       self.data     = json.loads(self.response.text)
       self.meta     = self.data['meta']
       self.objects  = self.data['objects']
       self.meta     = self.data['meta']
       self.objects  = self.data['objects']
        
   def accessor(self):
       return exceptions.NotImplementedError()

   def __iter__(self):
       for x in self.objects:
           yield Entry(x)

class Entry(object):

   def __init__(self, data):
       self.data = data
       self.resource_uri = data['resource_uri']
       self.accessor = hammock.Hammock(self.resource_uri, auth=(username,password))

   def __repr__(self):
       return repr(self.data)

class Organizations(Collection):

   def accessor(self):
       return self.handle.organizations

#(Epdb) got.text
#u'{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 1}, "objects": [{"active": true, "creation_date": "2013-03-15", "description": "testorg!", "id": 1, "name": "testorg", "resource_uri": "/api/v1/organizations/1/"}]}'
#

try:
    orgs = Organizations(handle)
    for x in orgs:
       print x
except requests.exceptions.ConnectionError:
    print "connect failed"
    sys.exit(1)

