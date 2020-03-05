# How to write modules

First of all, please have a look at the [Ansible module development](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html) guide and get familiar with the general Ansible module layout.

When looking at actual modules in this repository ([`foreman_domain`](plugins/modules/foreman_domain.py) is a nice short example), you will notice a few differences to a "regular" Ansible module:

* Instead of `AnsibleModule`, we use `ForemanEntityAnsibleModule` (and a few others, see [`plugins/module_utils/foreman_helper.py`](plugins/module_utils/foreman_helper.py)) which provides an abstraction layer for talking with the Foreman API
* Instead of Ansible's `argument_spec`, we provide an enhanced version called `entity_spec`. It handles the translation from Ansible module arguments to Foreman API parameters, as nobody wants to write `organization_ids` in their playbook when they can write `organizations`

The rest of the module is usually very minimalistic:

* Connect to the API (`module.connect()`)
* Find the entity if it already exists (`entity = module.find_resource_by_name(…)`)
* Adjust the data of the entity if desired
* Ensure the entity state and details (`changed = module.ensure_resource_state(…)`)

## Specification of the `entity_spec`

The `entity_spec` can be seen as an extended version of Ansible's `argument_spec`. It understands more parameters (e.g. `flat_name`) and supports more `type`s than the original version. An `argument_spec` will be generated from an `entity_spec`. Any parameters not directly known or consumed by `entity_spec` will be passed directly to the `argument_spec`.

In addition to Ansible's `argument_spec`, `entity_spec` understands the following types:

* `type='entity'` The referenced value is another Foreman entity.
This is usually combined with `flat_name=<entity>_id`.
* `type='entity_list'` The referenced value is a list of Foreman entities.
This is usually combined with `flat_name=<entity>_ids`.
* `type='nested_list'` The referenced value is a list of Foreman entities that are not included in the main API call.
The module must handle the entities separately.
See domain parameters in [`foreman_domain`](plugins/modules/foreman_domain.py) for an example.
The sub entities must be described by `entity_spec=<sub_entity>_spec`.
* `type='invisible'` The parameter is available to the API call, but it will be excluded from Ansible's `argument_spec`.

`flat_name` provides a way to translate the name of a module argument as known to Ansible to the name understood by the Foreman API.

You can add new or override generated Ansible module arguments, by specifying them in the `argument_spec` as usual.
