import os
import requests
from requests.auth import HTTPBasicAuth
import sys
import json

# this is temporary
username = os.getenv("ACOM_USER","admin")
password = os.getenv("ACOM_PASS","admin")
server   = os.getenv("ACOM_SERVER","http://127.0.0.1:8000")
PARAMS   = dict(format='json')
HEADERS  = { 'Content-Type' : 'application/json' }
AUTH     = HTTPBasicAuth(username, password)

# TODO: format into actual command line

# =============================================================
# wrappers around URL request functions

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

def update_item(item, data, expect=200):
   resp = requests.put("%s/%s" % (server, item.resource_uri), auth=AUTH, data=data, headers=HEADERS)
   if resp.status_code != expect:
       assert "PUT: Expecting %s got %s: %s" % (expect, resp.status_code, resp.text)
   return resp

def delete(url_seg, expect=204):
   print "DELETING: %s" % url_seg
   resp = requests.delete("%s/%s" % (server, url_seg), auth=AUTH, headers=HEADERS)
   if resp.status_code != expect:
       assert "DELETE: Expecting %s got %s: %s" % (expect, resp.status_code, resp.text)
   return resp

# =============================================================

class Collection(object):

   def __init__(self):

       self.response = get(self.base_url())
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

   def print_display(self):
       # TODO: paginate/flexible headers
       print "%s" % self.name()
       print "==="
       for x in self.objects:
           print Entry(x).display()
       print ""

class Entry(object):

   def __init__(self, data):
       self.data = data
       self.resource_uri = data.get('resource_uri', None)

   def __repr__(self):
       return repr(self.data)

   def update(self, data):
       json_data = json.dumps(data)
       return update_item(self, json_data)
        
   def delete(self):
       ''' deletes the resource '''
       return delete(self.resource_uri)

   def deactivate(self):
       return self.update(dict(active=False))

   def activate(self):
       return self.update(dict(active=True))

   def delete_membership(self, parent, field):
       ''' 
       removes this object from a parent collection:
       example project.delete_membership(org, 'projects')
       '''
       parent_uri = parent.resource_uri
       uri = "/".join(parent_uri, "/", field, self.data['id'])
       return delete(uri)

   def display(self):
       keyz = self.data.keys()
       keyz.sort()
       lines = []
       lines.append("    %20s" % self.resource_uri)
       lines.append("    %20s | %s" % ('name', self.data['name']))
       lines.append("    %20s | %s" % ('description', self.data['description']))
       lines.append("    %20s | %s" % ('creation_date', self.data['creation_date']))
       for key in keyz:
           if key not in [ 'name', 'description', 'id', 'resource_uri', 'creation_date' ]:
               lines.append("    %20s | %s" % (key, self.data[key]))
       return "\n".join(lines)

   def print_display(self):
       print self.display()

class Organizations(Collection):

   def name(self):
       return "Organizations"

   def base_url(self):
       return "organizations/"

class Projects(Collection):
   
   def name(self):
       return "Projects"

   def base_url(self):
       return "projects/"


#(Epdb) got.text
#u'{"meta": {"limit": 20, "next": null, "offset": 0, "previous": null, "total_count": 1}, "objects": [{"active": true, "creation_date": "2013-03-15", "description": "testorg!", "id": 1, "name": "testorg", "resource_uri": "/api/v1/organizations/1/"}]}'
#

try:

    print "*** adding an org"
    orgs = Organizations()
    orgs.add(dict(description="new org?", name="new org"))
    last_org = list(Organizations())[-1]  
    Organizations().print_display()

    print "*** adding a project"
    projects = Projects()
    projects.add(dict(description="new project?", name="new project"))
    last_project = list(Projects())[-1]

    last_project.update(dict(description="new project!!!!", name="new project!!!!", organization=last_org.resource_uri))
    Organizations().print_display()
   
    print "*** showing the orgs"
    Organizations().print_display()

    print "*** showing the projects"
    Projects().print_display()

    print "*** deleting all projects"
    [x.delete() for x in projects]

    print "*** showing the projects"
    Projects().print_display()

except requests.exceptions.ConnectionError:
    print "connect failed"
    sys.exit(1)

