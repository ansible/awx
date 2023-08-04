

.. follow outline below

**New Features**

- Administrative users can now enable a :ref:`tech preview of the new controller UI <ug_ui_main>`, which includes some basic and limited functionality around creating and viewing the resources needed to launch a job template (AAP-9133)
- A tech preview version of the Automation Calculator utility that shows a report that represents (possible) savings to the subscriber (AAP-7331) See :ref:`analytics_reports` for more information.
- IBM Z/Power support has been added as a tech preview feature for |aap| 2.4 and ARM support is added so you can now run |at| on an ARM machine with or without using the bundle installer (AAP-7975)
- Ability to :ref:`launch multiple jobs at once <ug_JobTemplates_bulk_api>` via a new API endpoint, ``/api/v2/bulk/job_launch`` (AAP-7953)
- Ability to :ref:`add multiple hosts at once <ug_inventories_add_host_bulk_api>` via a new API endpoint, ``/api/v2/bulk/host_create`` (AAP-5706)
- Provided a new page for showing which hosts are consuming the subscription count and allowing users to delete hosts that are no longer used so they are not counted against the subscription consumption (AAP-9046) See :ref:`subscription_compliance` for more information. 
- Introduced the ability to scale web and task pods independently (AAP-6025)
- Conjur Cloud support to CyberArk Conjur Secrets Lookup (AAP-6643) See :ref:`ug_credentials_cyberarkconjur` for detail.
- Added the ability to use host and groupvars in order to create :ref:`ug_inventories_constructed` from other inventories (AAP-3687)
- Added the ability to run automation against Constructed Inventories (AAP-3687)
- Added **Max concurrent jobs** and **Max forks** fields in the Instance Group and Container Groups *Create* and *Edit* screens of the controller UI to allow users to define an instance group maximum of jobs that will be run on an instance group or sum of forks of all jobs to be run an instance group, making this especially useful for container groups where there is no concept of capacity (AAP-6699) See :ref:`ag_instancegrp_cpacity` for more information.


**Additions**

- Added the ability for |at| to tolerate the restart of Kubernetes master node during job execution and as a result, jobs will no longer fail due to a master node restart (AAP-12590)
- The Add button is now available for organization Admins to be able to add roles to the team (AAP-11618)
- Missing API metrics related to ``task_manager``, ``dependency_manager``, and ``workflow_manager`` are added to the ``/api/v2/metrics/`` endpoint to standalone scenarios (AAP-10795)
- Added use of static Central Credential deployment for CyberArk on cloud (AAP-7272) See :ref:`ug_credentials_cyberarkccp` for more detail.
- Expanded the Advanced search capability in the controller UI to support the lookup type of **exact** on **related keys** (AAP-6886)


**Updates or Fixes**

- After database failover, the Dispatcher now recovers and resumes normal operation (AAP-12462)
- Users can now specify an SCM branch override on the inventory source and inventory update, similar to how it is done for job templates (AAP-9150) See :ref:`ug_inventory_sources` for detail.
- 'Normal' users now have the ability to select instance groups on job templates in the UI (AAP-5170)
- Changed the Operator to split web and task into separate deployments (aka Web-Task split). Redis now runs as a separate container inside of the pod in the OpenShift Container Platform . Now that web/task are separate pods, they now both have their own dedicated redis containers and use another service to clear cache (``clear_cache``) and restart rsyslog (``rsyslog_reconfigurer``). (awx-operator#1182)
- Requests to HashiCorp Vault clusters will be retried if an HTTP 412 error is received from the HashiCorp Vault server instead of failing (AAP-8503)
- Updated the controller UI to pre-populate information from a credential and inventory when creating a job template from the context of a credential or inventory, respectively (AAP-7286)
- Updated the Job Template form to allow the playbook filename to be manually entered even if those filenames are not present in the select list (AAP-5672)
- Improved the speed of saving facts to hosts at the end of a job, and ensured that facts are saved before the status changes so that downstream workflow nodes can make use of host fact saved by the prior node (AAP-9144)
- Removed validation check that was disallowing users from editing the hostname of a host attached to an inventory when the ``max_hosts`` limit was reached for a particular organization (AAP-4487)
- "Related Groups" column added back to "Hosts" views in the controller UI (AAP-4538)
- Re-added the **Approve** and **Deny** buttons to the list toolbar of the controller UI (AAP-8384)
- Added a password field to the user serializer if a user is an internal user. This allows for the ``awx.awx.user`` module to respect the ``update_secrets`` parameter. This also changes the ``/api/v2/users`` endpoint by adding a password field to the returned payload on a **GET** which will have a value of ``"$encrypted$"`` (awx#13704)
- Users logging in through LDAP are now properly being mapped into teams based on their LDAP groups (AAP-9067)
- The LDAP adapter no longer removes users from admin roles (and others) for an organization even if the ``remove_*`` flag was set to ``False`` (AAP-8696)
- The LDAP adapter no longer manages a team by name regardless of the organization the team was in, preventing users of a particular team from logging into the system through LDAP and being unnecessarily added to multiple organizations due to the same team name (AAP-8063)
- Improved performance of the SAML login process (AAP-4671)
- Jobs due to ``X509_V_FLAG_CB_ISSUER_CHECK`` attribute no longer produces an error (AAP-12618)
- Saving a workflow in the controller UI will no longer save an empty string for ``scm_branch``, which previously resulted in undesired changing of the branch jobs used (AAP-7638)
- Editing a node no longer defaults to *All Convergence* in the Workflow Visualizer of the controller UI (AAP-7243)
- Controller containers in an Openshift Container Platform now operate as expected when running 100 jobs or more (AAP-6406)
- When executing a playbook that contains multiple credentials in the job template, the correct error displays (AAP-5951)
- Triggered notifications perform a POST request during job template runs as expected (AAP-5785)
- Accessing the globally available execution environments no longer produces a 500 error or a 400 error while assigning the "Execution Environment Admin” permission to a user (AAP-2551)
- The frequency of the scheduler now run ons the correct day of the week as specified by the user (AAP-11776)
- Management jobs scheduled with a "days" parameter can now be edited (AAP-10338)
- Disabled schedules no longer lose access to encrypted survey values (AAP-4501)
- Fixed the date picker to no longer select dates in the past and prevent saving (AAP-4499)
- Thycotic Secret Server credential type can now handle secret types such as SSH key or Digital Certificate in addition to just Password templates (AAP-11711 and AAP-11795)
- Changing credential types using the dropdown list in the Launch prompt window no longer causes the screen to disappear (AAP-11444)
- Fixed broken name search in the credentials step of ad-hoc commands and updated adhoc credentials search queries to include **icontains** (AAP-9668)
- Missing Vault ID in the credential edit form no longer prevents vault credential to update properly (AAP-11438)
- Viewing job details of a job template that has been deleted no longer displays an error (AAP-7236)
- Variables in the controller UI can now be edited in YAML format (AAP-5540)
- The login form no longer supports auto-complete on the password field due to security concerns (AAP-5437)
- Corrected the behavior of the controller UI to no longer display the "waiting" status while a job is running (AAP-5273)
- The controller now tolerates resume streaming stdout from job execution container after being disconnected from Kubernetes API server (AAP-5116)
- Corrected broken docs link in the controller UI during product registration (AAP-4903)
- The job output in the controller UI is now updating correctly despite to gap between API-loaded job events and WS-streamed events (AAP-4730)


**Deprecations**

.. repo #issue

- Smart Inventories are deprecated in favor of :ref:`ug_inventories_constructed`


**Removals**

- Removed auto-complete for fields in the controller UI to prevent exposing sensitive information (AAP-8543)
