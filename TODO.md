TODO items for ansible commander
================================

* tastypie subresources?  Maybe not.  Are they needed?

* tastypie authz (various subclasses) using RBAC permissions model

  ** for editing, is user able to edit the resource
  ** if they can, did they remove anything they should not remove or add anything they cannot add?
  ** did they set any properites on any resources beyond just creating them?

* tastypie tests using various users

* CLI client
* business logic 
* celery integration / job status API
* UI layer
* clean up initial migrations

NEXT STEPS

* Michael -- REST resources, REST auth, CLI/client lib
* Chris -- celery infra, use db queue if possible?
