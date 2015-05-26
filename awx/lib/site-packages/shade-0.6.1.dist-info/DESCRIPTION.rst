shade
=====

shade is a simple client library for operating OpenStack clouds. The
key word here is *simple*. Clouds can do many many many things - but there are
probably only about 10 of them that most people care about with any
regularity. If you want to do complicated things, you should probably use
the lower level client libraries - or even the REST API directly. However,
if what you want is to be able to write an application that talks to clouds
no matter what crazy choices the deployer has made in an attempt to be
more hipster than their self-entitled narcissist peers, then shade is for you.

shade started its life as some code inside of ansible. ansible has a bunch
of different OpenStack related modules, and there was a ton of duplicated
code. Eventually, between refactoring that duplication into an internal
library, and adding logic and features that the OpenStack Infra team had
developed to run client applications at scale, it turned out that we'd written
nine-tenths of what we'd need to have a standalone library.

example
-------

Sometimes an example is nice.
::

  from shade import *
  import time

  # Initialize cloud
  # Cloud configs are read with os-client-config
  cloud = openstack_cloud('mordred')

  # OpenStackCloud object has an interface exposing OpenStack services methods
  print cloud.list_servers()
  s = cloud.list_servers()[0]

  # But you can also access the underlying python-*client objects
  cinder = cloud.cinder_client
  volumes = cinder.volumes.list()
  volume_id = [v for v in volumes if v['status'] == 'available'][0]['id']
  nova = cloud.nova_client
  print nova.volumes.create_server_volume(s['id'], volume_id, None)
  attachments = []
  print volume_id
  while not attachments:
      print "Waiting for attach to finish"
      time.sleep(1)
      attachments = cinder.volumes.get(volume_id).attachments
  print attachments



