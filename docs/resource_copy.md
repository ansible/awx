Starting from Tower 3.3 and API V2, users are able to copy some existing resource objects to quickly
create new resource objects via POSTing to the corresponding `/copy/` endpoint. A new `CopyAPIView` class
is introduced as the base view class for `/copy/` endpoints. It mimics the process of manually fetching
fields from the existing object to create a new object, plus the ability to automatically detect sub
structures of existing objects and make a background task-based deep copy when necessary.


## Usage

If an AWX resource is able to be copied, all of its object detail API views will have a related URL field
`"copy"`, which has the form `/api/v2/<resource name>/<object pk>/copy/`. A GET to this endpoint
will return `can_copy`, which is a boolean indicating whether the current user can execute a copy
operation; POSTing to this endpoint actually copies the resource object. One field, `name`, is required;
this will later be used as the name of the created copy. Upon success, a 201 will be returned, along
with the created copy.

For some resources like credentials, the copy process is not time-consuming, thus the entire copy
process will take place in the request-response cycle, and the created object copy is returned as a
POST response.

For some other resources like inventories, the copy process can take longer, depending on the number
of sub-objects to copy (this will be explained later in this document). Thus, although the created copy will be returned, the
copy process is not finished yet. All sub-objects (like all hosts and groups of an inventory) will
not be created until after the background copy task is finished successfully.

Currently, the available list of copiable resources are:

- job templates
- projects
- inventories
- workflows
- credentials
- notifications
- inventory scripts

For most of the resources above, only the object to be copied itself will be copied; for some resources
like inventories, however, sub resources belonging to the resource will also be copied to maintain the
full functionality of the copied new resource. Specifically:

- When an inventory is copied, all of its hosts, groups and inventory sources are copied.
- When a workflow job template is copied, all of its workflow job template nodes are copied.


## How to Add a Copy Endpoint for a Resource

The copy behavior of different resources largely follow the same pattern, therefore a unified way of
enabling copy capability for resources is available for developers.

First, create a `/copy/` URL endpoint for the target resource.

Second, create a view class as handler to the `/copy/` endpoint. This view class should be subclassed
from `awx.api.generics.CopyAPIView`. Here is an example:
```python
class JobTemplateCopy(CopyAPIView):

    model = JobTemplate
    copy_return_serializer_class = JobTemplateSerializer
```

Note the above example declares a custom class attribute `copy_return_serializer_class`. This attribute
is used by `CopyAPIView` to render the created copy in POST response, so in most cases the value should
be the same as `serializer_class` of corresponding resource detail view; for example, here the value is the
`serializer_class` of `JobTemplateDetail`.

Third, for the underlying model of the resource, add two macros, `FIELDS_TO_PRESERVE_AT_COPY` and
`FIELDS_TO_DISCARD_AT_COPY`, as needed. Here is an example:
```python
class JobTemplate(UnifiedJobTemplate, JobOptions, SurveyJobTemplateMixin, ResourceMixin):
    '''
    A job template is a reusable job definition for applying a project (with
    playbook) to an inventory source with a given credential.
    '''
    FIELDS_TO_PRESERVE_AT_COPY = [
        'labels', 'instance_groups', 'credentials', 'survey_spec'
    ]
    FIELDS_TO_DISCARD_AT_COPY = ['vault_credential', 'credential']
```
When copying a resource object, basically all fields necessary for creating a new resource (fields
composing a valid POST body for creating new resources) are extracted from the original object and
used to create the copy.

However, sometimes we need more fields to be copied, like `credentials` of a job template, which
cannot be provided during creation. In this case we list such fields in `FIELDS_TO_PRESERVE_AT_COPY`
so that these fields won't be missed.

On the other hand, sometimes we do not want to include some fields provided in create POST body,
like `vault_credential` and `credential` fields used for creating a job template, which do not have
tangible field correspondence in `JobTemplate` model. In this case we list such fields in
`FIELDS_TO_DISCARD_AT_COPY` so that those fields won't be included.

For models that will be part of a deep copy, like hosts and workflow job template nodes, the related
POST body for creating a new object is not available. Therefore all necessary fields for creating
a new resource should also be included in `FIELDS_TO_PRESERVE_AT_COPY`.

Lastly, unit test copy behavior of the new endpoint in `/awx/main/tests/functional/test_copy.py` and
update docs (like this doc).

Fields in `FIELDS_TO_PRESERVE_AT_COPY` must be solid model fields, while fields in
`FIELDS_TO_DISCARD_AT_COPY` do not need to be. Note that there are hidden fields not visible from the model
definition, namely reverse relationships and fields inherited from super classes or mix-ins. A help
script `tools/scripts/list_fields.py` is available to inspect a model and list details of all its
available fields:
```
# In shell_plus
>>> from list_fields import pretty_print_model_fields
>>> pretty_print_model_fields(JobTemplate)
```

`CopyAPIView` will automatically detect sub objects of an object, and do a deep copy of all sub objects
as a background task. There are sometimes permission issues with sub object copy. For example,
when copying nodes of a workflow job template, there are cases where the user performing copy has no use for
permission of related credential and inventory of some nodes, and those fields should be
`None`. In order to do that, the developer should provide a static method `deep_copy_permission_check_func`
under corresponding specific copy view:
```python
class WorkflowJobTemplateCopy(WorkflowsEnforcementMixin, CopyAPIView):

    model = WorkflowJobTemplate
    copy_return_serializer_class = WorkflowJobTemplateSerializer

    # Other code

    @staticmethod
    def deep_copy_permission_check_func(user, new_objs):
        # method body

    # Other code
```
Static method `deep_copy_permission_check_func` must have and only have two arguments: `user`, the
user performing the copy, and `new_objs`, a list of all sub objects of the created copy. Sub objects in
`new_objs` are initially populated disregarding any permission constraints; the developer shall check
`user`'s permission against these new sub objects and unlink related objects or send
warning logs as necessary. `deep_copy_permission_check_func` should not return anything.

Lastly, macro `REENCRYPTION_BLOCKLIST_AT_COPY` is available as part of a model definition. It is a
list of field names which will escape re-encryption during copy. For example, the `extra_data` field
of workflow job template nodes.


## Acceptance Criteria

* Credentials should be able to copy themselves. The behavior of copying credential A shall be exactly
  the same as creating a credential B with all necessary fields for creation coming from credential A.
* Inventories should be able to copy themselves. The behavior of copying inventory A shall be exactly
  the same as creating an inventory B with all necessary fields for creation coming from inventory A. Other
  than that, inventory B should inherit A's `instance_groups`, and have exactly the same host and group
  structures as A.
* Inventory scripts should be able to copy themselves. The behavior of copying inventory script A
  shall be exactly the same as creating an inventory script B with all necessary fields for creation
  coming from inventory script A.
* Job templates should be able to copy themselves. The behavior of copying job template A
  shall be exactly the same as creating a job template B with all necessary fields for creation
  coming from job template A. Other than that, job template B should inherit A's `labels`,
  `instance_groups`, `credentials` and `survey_spec`.
* Notification templates should be able to copy themselves. The behavior of copying notification
  template A shall be exactly the same as creating a notification template B with all necessary fields
  for creation coming from notification template A.
* Projects should be able to copy themselves. The behavior of copying project A shall be the
  same as creating a project B with all necessary fields for creation coming from project A, except for
  `local_path`, which will be populated by triggered project update. Other than that, project B
  should inherit A's `labels`, `instance_groups` and `credentials`.
* Workflow Job templates should be able to copy themselves. The behavior of copying workflow job
  template A shall be exactly the same as creating a workflow job template B with all necessary fields
  for creation coming from workflow job template A. Other than that, workflow job template B should
  inherit A's `labels`, `instance_groups`, `credentials` and `survey_spec`, and have exactly the
  same workflow job template node structure as A.
* In all copy processes, the `name` field of the created copy of the original object should be customizable in the POST body.
* The permission for a user to make a copy for an existing resource object should be the same as the
  permission for a user to create a brand new resource object using fields from the existing object.
* The RBAC behavior of original workflow job template `/copy/` should be pertained. That is, if the
  user has no permission to access the related project and credential of a workflow job template
  node, the copied workflow job template node should have those fields empty.
