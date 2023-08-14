.. _release_notes:

**************
Release Notes
**************

.. index::
   pair: release notes; v4.0
   pair: release notes; v4.0.1
   pair: release notes; v4.1
   pair: release notes; v4.1.1
   pair: release notes; v4.1.2
   pair: release notes; v4.1.3
   pair: release notes; v4.1.4
   pair: release notes; v4.2.0
   pair: release notes; v4.2.1
   pair: release notes; v4.3.0
   pair: release notes; v4.3.1
   pair: release notes; v4.3.2
   pair: release notes; v4.3.3
   pair: release notes; v4.3.4
   pair: release notes; v4.3.5
   pair: release notes; v4.3.6
   pair: release notes; v4.3.7
   pair: release notes; v4.3.8
   pair: release notes; v4.3.9
   pair: release notes; v4.4


Automation Controller Version 4.4
===================================

.. include:: ../common/relnotes_current.rst


Automation Controller Version 4.3.9
====================================

**General Fixes**

- Allow configuration of resource requirements for init containers 
- Added ``postgres_storage_class`` to the OpenShift UI and fixed PostgreSQL Storage requirements display 

**Automation Controller fixes:**

- The **Days** parameter in management jobs schedules can now be edited 
- Fixed an error message in the Host Event window when job event stdout is an array 
- Turned off login password auto-complete 
- Fixed an error that was shown to Org Admin users on the Instances list 
- Fixed incorrectly displayed workflow job within workflow approval details 
- Removed case-sensitive credential name search in ad-hoc commands prompts 
- Using the **Back to list** button now maintains previous search filters 
- Topology view and Instances are only available as options on the left navigation menu options to System Administrators and System Auditors 


Automation Controller Version 4.3.8
====================================

**General Fixes**

- Receptor TLS errors when run with FIPS enforced in the Operator 

**Automation Controller fixes:**

- Automation controller now requires git-core instead of git 


Automation Controller Version 4.3.7
====================================

**General Fixes**

- Nginx ``ssl_protocols`` now defaults to TLSv1.2 and is configurable 
- Added supervisor_start_retry_count for supervisord 
- Increased the HSTS duration to 2 years and is now configurable 
- Made ``client_max_body_size`` for controller nginx configurable at install time for the VM installer, and the Operator default value has been increased to 5 MB 

.. sources: review inputs from Satoe and Christian Adams

**Automation Controller fixes:**

- Manifest upload in the controller no longer fails when the manifest size is over 1MB 
- Fixed race condition with heartbeat and reaper logic 
- Fixed bug where users were unable to toggle variables between JSON and YAML in the UI 
- Reformatted the Backup CR and persistent volume claim PVC options on AutomationControllerRestore 
- Backup role now uses ``k8s_cp`` module to write large files 
- Backups on AAP Operator no longer fails when filesystem is ext4 

.. sources: RHBA-2023:1315, RHBA-2023:1518, RHBA-2023:1635,1636


Automation Controller Version 4.3.6
====================================

**Automation Controller fixes:**

- Allowed the CLI to export schedule fields when exporting job templates 
- Users logging in through LDAP are now properly mapped to teams based on their LDAP groups 
- Improved performance and properly updated job status for facts gathering to avoid missing facts 


Automation Controller Version 4.3.5
====================================

**Automation Controller fixes:**

- LDAP login no longer adds or removes a user from any team in the system with the same name as the LDAP team being managed 
- Updated Django, GitPython and Wheel in virtual environments 
- LDAP Adapter now respects remove flag in configuration 
- Performance has been improved for SAML configuration 


**Automation Controller UI fixes**:


- Fixed a bug where the date picker would select dates in the past and prevent saving 
- Workflow Approve/Deny bulk actions were added back to Workflow Approvals list 
- UI no longer shows 'TypeError' error message when a task in Job Output console is clicked on running jobs 
- Fixed duplicate key value errors to properly produce job stdout while launching a job template 
- Navigating to an instance in an instance group's list no longer produces a ``404`` error


Automation Controller Version 4.3.4
===================================

**Automation Controller fixes:**

- Starting the application no longer results in 'listener_port' not-null constraint violation error 
- Shell escaping no longer produces special characters in the Administrator password 


Automation Controller Version 4.3.3
===================================

**Automation Controller fixes:**

- Accessing ees functions as expected when upgrading from Ansible Tower 3.x 
- Updated the receptor to 1.3.0-3 to avoid replacing ``receptor.conf`` on upgrade 


**Automation Controller UI fixes**:

- The **Save** button now responds appropriately on the Job Settings page 


Automation Controller Version 4.3.2
===================================

**Automation Controller UI fixes**:

- Fixed the Job Template Launch page to no longer result in a 'Not Found' error when choosing credentials 


Automation Controller Version 4.3.1
===================================

**Automation Controller fixes:**

- Fixed issue upgrading

**Automation Controller UI fixes**:

- The Hosts Automated field is now correctly translated


Automation Controller Version 4.3 
===================================

**New Features**

.. awx #12610:

- Added the ability for control nodes to peer out to remote execution nodes on a Kubernetes deployment only

.. tower #6038:

- Introduced peers detail tab for instances

.. tower #6036:

- Introduced the ability to create and remove instances in the controller UI

.. tower #5975:

.. tower #6045, 6044, 6043, 6042:

- Updated nodes/links in the Topology Viewer of the controller UI to support new states

.. awx #12739:

- Enabled health checks to be run on remote execution nodes on a Kubernetes deployment 

- Added the ability for Kubernetes users to create instance groups

.. awx #11695 #12487 #12482 #12485 #12691 #12484 #12590 #12536:

- Added project/playbook signature verification functionality to the controller, enabling users to supply a GPG key and add a content signing credential to a project, automatically enabling content signing for that project

.. awx #12488:

- Introduced ``ansible-sign``, a content signing and verification utility that provides a unified way to sign content across the Ansible eco-system

.. tower #5673:

- Support for schedules with the ``awx-cli import`` and ``awx-cli export`` features

.. awx #12299:

- Surfaced database connections in ``/api/v2/metrics``


**Additions**

.. tower #5991:

- Topology viewer now shows new node and link states

.. tower #5976:

- Mesh topology shows directionality of links between nodes

.. awx #4481:

- The ability to pass variable value from a nested workflow job template to a job template or workflow job template using the ``set_stats`` module

.. tower #5859:

- Added **Prompt on Launch** options on all parameters of the job template and workflow job templates 

.. awx #11423:

- Added Job and Skip tags on workflow job templates and accompanying **Prompt on Launch** options

.. tower #5777:

- Configurable timeout settings for the receptor

.. tower #5268:

- Added missing security headers to application URLs

.. 

- Metrics added for Support Engineers and customers to analyze, problem solve performance-related issues with lags in job events

.. awx #12543 #12556:

- The controller now polls the job endpoint to determine exactly when events are done processing and the UI displays a message when it has finished processing events for the job

.. tower #4644:

- Include forks on job and/or job template data for Automation Analytics

.. tower #5905:

- Forks information no longer missing in running job details

.. awx #12542:

- Schedules now allow date exceptions

.. awx #12201:

- Optimized/cache information about preferred instance groups

.. tower #5970:

- Control for capacity decisions and task worker availability

.. tower #5610:

- Survey wizard now handles multiple choice/multi-select question-answers in both array and string form formerly only strings were supported

.. awx #8097:

- Surveys can now auto-complete in multiple choice input fields

.. tower #5609:

- Added options for setting the priority class on the control plane and PostgreSQL pods

.. tower-packaging #1718:

- Added the ability for Receptor Ansible collection to provision receptor nodes

.. tower #6075:

- Added the ability to deprovision external execution nodes

.. tower-packaging #1734 and awx #12612:

- Added playbook with all the required variables for provisioning new remote execution nodes

.. awx #11861 #11862 #11863 #11866 #11867 #11868 #11869 #11870 #11871 #11872 #11873 #11874:

- Pop-up help text added to Details fields of job templates, workflow job templates, credentials, projects, inventories, hosts, organizations, users, credential types, notifications, instance groups, applications, and ees

.. tower #5840:

- Extra variables added to workflow approval notifications


**Updates or Fixes**

.. tower #6044 #6045 #6042:

- Topology Viewer links, nodes, legend, list view "Status" updated to reflect new states

.. tower #6043

- Updated the Topology viewer to show more node detail 

.. tower #5986:

- Topology Viewer no longer fails to populate when launched

.. tower #6092:

- Updated the controller to handle asynchronous health checks on an instance

.. awx #12847:

- Nodes are now moved to a deprovisioning state when removing from the controller UI

.. tower #5838:

- Increased the number of allowed characters for the ``job_tags`` Job Tags field in a template

.. tower #5811:

- Job schedules are no longer missing from the Schedules view when sorting by type 

.. awx #11990:

- Schedules now prompting for job or skip tags

.. awx #12336:

- Browser timezone automatically set as default when creating a schedule

.. awx #13002:

- Fixed issue with adding a schedule to an inventory source

.. tower #5924:

- LDAP / LDAPS connections no longer stay open after a user has logged out

.. tower #3434:

- Refactored LDAP backend to be more efficient, including reduced initial login time after increasing list of LDAP mappings

.. awx #12690:

- Job launch failure error now contains more succinct and informative messaging in the event that content signature validation fails

.. awx #12876:

- Users with Admin permissions on a workflow are able to assign an inventory to the workflow job template

.. awx #12512:

- Approval node toolbar buttons updated to improve the Workflow approval user experience

.. awx #7946:

- Workflow approval templates are now exportable

.. tower #5962:

- Admin users can now copy a workflow job template

.. awx #4294:

- Node rejoins cluster as expected after connection to PostgreSQL is lost

.. awx #12710 tower #6015

- Workflow or sliced jobs no longer blocked or fails when ran

.. tower #4598:

- Sliced jobs no longer produce `500` errors when performing a ``GET`` operation while launching more than 500 slices

.. awx #13131:

- Jobs no longer fails if Job Slicing and Fact Storage are enabled together

.. awx #12575:

- Adhoc command jobs no longer result in error when ran

.. awx #13033:

- Fixed error that resulted from relaunching an adhoc command with password

.. awx #9222:

- Advanced search updated to only allow users to select valid or logical match types to avoid unnecessary `500` errors

.. tower #5943:

- Included updates and enhancements to improve performance associated with the Task Manager in the handling of scaling jobs, mesh and cluster sizes

.. awx #11629:

- Job output performance improvements

.. awx #11822:

- Job output screen user experience improvements

.. awx #12129:

- Job timeout details showing in the Job Output as expected

.. awx #10192:

- Job Settings page updated to no longer produce `404` errors and other various warnings

.. awx #11978:

- First Run / Next Run values of the job schedule fixed to no longer change to one day before the date entered in the Edit/Add page of the schedule settings

.. tower #4579:

- Job template with concurrent jobs launches as expected if capacity allows the controller to run more jobs

.. tower #5889 and #5890:

- ``awx-cli import`` and ``awx-cli export`` now produce an error message and provide appropriate exit codes when an imported or exported operation fails

.. awx #12802:

- Default cleanup schedules no longer only run once

.. awx #12519:

- Updated SAML adapter to not remove System Administrator and System Auditor flags

.. awx #10093:

- Lookup modals refresh when opened

.. tower #5708:

- Twilio notifications can now be sent from the controller from behind a proxy

.. tower #5907:

- Custom credential type creation works as expected

.. tower #5942:

- Updated strings for translation

.. tower #5807:

-  The Demo Project will now initially show a status of "successful" and will not update on launch, whereas before it showed "never updated" and updated on launch

.. awx #12413:

- Inventory updates based on an SCM source now provides the revision of the project it used

.. tower #5887:

- Removing hosts from inventories no longer fails with "Out of Shared Memory" error

.. tower #5862:

- Manually gathering analytics from CLI no longer results in a unicode error

.. tower #5844:

- Filter websockets related to sync jobs on jobs lists when refreshed, these jobs will be filtered again from the Jobs view

.. awx #12211:

- The ``GOOGLE_APPLICATION_CREDENTIALS`` environment variable is now being set from a Google Compute Engine GCE credential type

.. tower #6020:

- Fixes some stability issues with ansible-runner worker processes and related logging slowdowns in the Dispatcher task processing


**Deprecations**

None in this release.


**Removals**

.. awx #12206 #12436:

- Removed the **Update on Project Update** field ``update_on_project_update`` in projects. This is intended to be replaced by ordinary "Update on Launch" behavior, because they chain from inventory to project. So if this option was previously set on the inventory source, it is recommended that both inventory and project are set to "Update on Launch". 

.. tower #5883:

- The Credential Permissions page no longer allows Credential Admin or Org Admins to manage access operations for a credential that does not belong to any organization 

.. awx #6134:

- Fallback behavior removed when an instance group is defined on a job template or inventory


Automation Controller Version 4.2.1 
=====================================

**Automation Controller fixes:**

- Node alias is now saved when job template is changed in the workflow
- Improved error messages in the API ``job_explanation`` field for specific error scenarios, e.g., runner worker process is killed, or certain failure scenarios e.g., shutdown
- Fixed the Task Manager to fully account for the job's control process capacity for jobs running in container groups
- Fixed a few bugs that caused delays in task processing by adding the following file-based settings:
	- ``JOB_WAITING_GRACE_PERIOD`` increases the threshold for marking jobs stuck in the "waiting" status as failed
	- ``CLUSTER_NODE_MISSED_HEARTBEAT_TOLERANCE`` to allow the heartbeat to be more tolerant to clock skew and other problems
	- ``K8S_POD_REAPER_GRACE_PERIOD`` to allow more time before pod cleanup executes its last attempt to delete pods used by jobs
	- ``TASK_MANAGER_TIMEOUT`` to allow more time in the unlikely event that the Task Manager fails to finish normally

- Jobs no longer fail for nested submodules in an SCM git project and the ``.git`` folder will be omitted
- Added more logs to help debug database connectivity problems and cluster resource limits
- Removed the ``current_user`` cookie which was not used by the UI
- Updated controller to send FQCN data for tasks to analytics 
- Fixed the metrics endpoint ``/api/v2/metrics`` to no longer produce erroneous ``500`` errors
- Added ``remove_superuser`` and ``remove_system_auditors`` to the SAML user attribute map
- Added the ability to allow multiple values in the ``SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR.is_*_[valuerole]`` settings
- Unwanted Galaxy credentials are no longer added to the Organization while logging in through SAML
- awx-cli now allows for multiple ``--extra_vars`` parameters
- Receptor no longer fails in FIPS mode
- If an OCP node's record is deleted either by the ``awx-manage`` command or by the heartbeat task, it will re-register itself
- Upgrading and changing ``node_type`` from ``execution`` to ``control`` or ``hybrid`` no longer causes cleanup errors


**Execution Environment fixes**:

None for this release


**Automation Controller UI fixes**:

- The controller UI properly displays job output when ``strategy: free`` is set in the playbook
- Fixed the pagination displays within the main lists, i.e., Resources Job Templates, Projects, Inventory, Access Organization, Users, Teams, Notifications, and Administration Instance Groups, EEs
- Fixed the Job Output to properly follow and scroll; and improved the Page Up/Page Down button behavior
- Fixed the controller UI to now be able to filter by multiple labels 
- Large workflow templates no longer cause browsers to crash when linking nodes near the end of the template
- Fixed the approval node "Deny" to no longer run the subsequent workflow nodes
- Forks information no longer missing in running job details
- Upon saving a schedule, the date chooser no longer changes to the day before the selected date
- References to Ansible Tower are replaced with Automation Controller throughout the UI, including tooltips where documentation is referenced
- Corrected translations for the Japanese settings screen


**Installation fixes specific to Automation Controller**:

None for this release


Automation Controller Version 4.2 
===================================

**Introduced**

- Graphical visualization of the automation topology to show the types of nodes, the links between them and their statuses


**Added**

- For VM-based installs, the controller will now automatically mount the system trust store in ees when jobs run
- **Log Format For API 4XX Errors** field to the Logging settings form to allow customization of 4xx error messages that are produced when the API encounters an issue with a request
- Ability to use labels with inventory
- Ability to flag users as superusers and auditors in SAML integration
- Support for expanding and collapsing plays and tasks in the job output UI
- Filtering job output UI by multiple event types
- Various default search filters to a number of list views
- Top-level list of instances to now be visible in the UI
- A pop-up message when a user copies a resource
- Job Templates tab to Credentials and Inventories to view all the templates that use that particular credential or inventory


**Updated**

- Controller to use Python 3.9
- Django's ``SESSION_COOKIE_NAME`` setting to a non-default value. **Note**, any external clients that previously used the ``sessionid`` cookie will need to change. Refer to :ref:`api_session_auth` for more detail.
- Controller to support podman-style volume mount syntax in the **Paths to expose to isolated jobs** field of the Jobs Settings of the UI
- Isolated path to be exposed in OCP/K8s as HostPath
- Upgraded Django from version 2.2 to 3.2
- Modified usage of ``ansible_facts`` on Advanced Search to add more flexibility to the usage of ``ansible_facts`` when creating a smart inventory
- The controller node for a job running on an execution node now incurs a penalty of 1 unit of capacity to account for the system load that controlling a job incurs. This can be adjusted with the file-based setting ``AWX_CONTROL_NODE_TASK_IMPACT``.
- Project updates to always run in the ``controlplane`` instance group
- Slack notifications to allow replying to a thread instead of just channels
- UI performance to improve job output
- Job status icons to be more accessible
- Display of only usable inventories when launching a job
- Browser tab to show more information about which page the user is currently viewing
- Controller to now load variables *after* job template extra variables to prevent overriding the meta variables injected into each job run


**Deprecated**

- The concept of "committed capacity" from Instance Groups due to the removal of RabbitMQ
- Inventory source option to **Update on project update** - this field updates the inventory source if its project pulled a new revision. In the future, when updating an inventory source, the controller shall automatically run project updates if the project itself is set to **Update on launch**.


**Removed**

- Case sensitivity around hostcount

**Automation Controller fixes:**

- When setting the use role on a credential to more than 10 users, users are no longer added on different admin roles unexpectedly

- Fixed the fallback cleanup task to not delete files in-use

- Updated inventory hosts to allow editing when organization is at max host limit

- Enabled job slicing with fact caching now correctly saves facts for hosts from the relevant slice

- No longer validating hostnames when editing the hostname on an existing host


**Execution Environment fixes:**

- Fixed jobs stuck in running when timing out during an image pull 


**Automation Controller UI fixes:**

- Fixed list search/pagination filters in place when clicking the **Back to <N>** button. Applies to all top-level list pages except the Schedules page.

- Survey wizard now handles multiple choice/multi-select question-answers in both array and string form formerly only strings were supported

- Fixed error that resulted from relaunching an adhoc command with password

- Updated filter websockets related to sync jobs on jobs lists that when refreshed, these jobs will be filtered again from the Jobs view

- Added validation for same start/end day different time schedules


Automation Controller Version 4.1.3 
====================================

**Automation Controller fixes:**

- Receptor no longer fails in FIPS mode
- Added the ability to exit gracefully and recover quickly when a service in the control plane crashes
- The ``create_partition`` method will skip creating a table if it already exists
- Having logging enabled no longer breaks migrations if the migration sends logs to an external aggregator
- Fixed the metrics endpoint ``/api/v2/metrics`` to no longer produce erroneous ``500`` errors

**Execution Environment fixes:**

- Enhanced the ee copy process to reduce required space in the ``/tmp`` directory
- Allowed ee images to be pulled from at only
- Added the **ansible-builder-rhel8** image to the setup bundle
- Modified base ee images so that controller backups can run in the container


**Automation Controller UI fixes:**

- Upon saving a schedule, the date chooser no longer changes to the day before the selected date
- Fixed the ability to create manual projects in Japanese and other supported non-English languages
- Forks information no longer missing in running job details
- Project selected for deletion is now removed as expected when running a project sync
- The **Admin** option in the Team Permissions is now disabled so that a user cannot select it when it is not applicable to the available organizations
- Large workflow templates no longer cause browsers to crash when linking nodes near the end of the template
- References to Ansible Tower are replaced with Automation Controller throughout the UI, including tooltips where documentation is referenced


**Installation fixes specific to Automation Controller:**

- Updated the Receptor to 1.2.3 everywhere as needed


Automation Controller Version 4.1.2 
=====================================

**Automation Controller fixes**:

- Upgraded Django version to 3.2 LTS
- System management jobs are now able to be canceled 
- Rsyslog no longer needs manual intervention to send out logs after hitting a 40x error
- Credential lookup plugins now respect the ``AWX_TASK_ENV`` setting
- Updated Receptor version to 1.2.1, which includes several fixes

**Execution Environment fixes**:

- The host trusted cert store is now exposed to ees by default. See :ref:`ag_isolation_variables` for detail.
- Mounting the ``/etc/ssh`` or ``/etc/`` to isolated jobs now works in podman
- User customization of ee mount options and mount paths are now supported
- Fixed SELinux context on ``/var/lib/awx/.local/share/containers`` and ensure awx as podman storage 
- Fixed failures to no longer occur when the semanage ``fcontext`` has been already set for the expected directory

**Automation Controller UI fixes**:

- Fixed the ability to create manual projects in Japanese and other suppported non-English languages 
- Fixed the controller UI to list the roles for organizations when using non-English web browsers
- Fixed the job output to display all job type events, including source control update events over websockets
- Fixed the ``TypeError`` when running a command on a host in a smart inventory
- Fixed the encrypted password in surveys to no longer show up as plaintext in the Edit Order page

**Installation fixes specific to Automation Controller**:

- Fixed duplicate Galaxy credentials with no default organization
- Running the ``./setup.sh -b`` out of the installer directory no longer fails to load group vars
- The installer no longer fails when IPV6 is disabled
- Fixed unnecessary ``become_user:root`` entries in the installation
- Modified database backup and restore logic to compress dump data
- Creating default ees no longer fails when password has special characters
- Fixed installations of ees when installing without internet access
- Upgrading to AAP 2.1 no longer breaks when the Django superuser is missing
- Rekey now allowed with existing key


Automation Controller Version 4.1.1 
=====================================

- Added the ability to specify additional nginx headers

- Fixed analytics gathering to collect all the data the controller needed to collect

- Fixed the controller to no longer break subsequent installer runs when deleting the demo organization


Automation Controller Version 4.1 
===================================

..   - Improved
..   - Updated
..   - Added
..   - Introduced
..   - Deprecated
..  - Removed
..   - Fixed

.. commented out the above listing so that it can remain as a guide of terms to use consistently for all relnotes
.. these comments must stay at the bottom of this section, else the relnotes don't render properly
.. values of "Improved, Updated, Added, Introduced, Deprecated, Removed, Fixed" to be used as entries for all release notes


**Introduced**

- Connected Receptor nodes to form a control plane and execution :term:`mesh` configurations
- The special ``controlplane`` instance group to allow for the task manager code to target an OpenShift Controller node to run the project update
- The ability to render a configured mesh topology in a graph in the installer
- Controller 4.1 execution nodes can be remote
- Node types for Controller 4.1 ``control, hybrid, execution, hop``, ``control``, ``hybrid``, ``execution``, ``hop`` installed for different sets of services and provide different capabilities, allowing for scaling nodes that provide the desired capability such as job execution or serving of web requests to the API/UI. 


**Added**

- The ability for the platform installer to allow users to install execution nodes and express receptor mesh topology in the inventory file. The platform installer will also be responsible for deprovisioning nodes.
- Work signing to the receptor mesh so that control plane nodes have the exclusive authority to submit receptor work to execution nodes over the mesh
- Support for pre-population of ee name, description, and image from query parameters when adding a new ee in the Controller User Interface
- Ability to trigger a reload of the topology configuration in Receptor without interrupting work execution
- Using Public Key Infrastructure PKI for securing the Receptor mesh
- Added importing ees from ah into the controller to improve the platform experience


**Updated**

- The controller to support new controller control plane and execution mesh
- Task manager will only run project updates and system jobs on nodes with ``node_type`` of "control" or "hybrid"
- Task manager will only run jobs, inventory updates, and ad hoc commands on nodes with ``node_type`` of "hybrid" or "execution"
- Heartbeat and capacity check to work with Receptor execution nodes
- Reaper to work with the addition of execution nodes
- Controller User Interface to not show control instances as an option to associate with instance groups
- The Associate pop-up screen to display host names when adding an existing host to a group
- Validators for editing miscellaneous authentication parameters
- Advanced search key options to be grouped
- SAML variables default values 
- Survey validation on Prompt on Launch
- Login redirect


**Deprecated**

- None


**Removed**

- The ability to delete the default instance group through the User Interface 


Automation Controller Version 4.0.1 
=====================================

- Upgraded Django version to 3.2 LTS
- Updated receptor to version 1.2.1


Automation Controller Version 4.0 
===================================

..   - Improved
..   - Updated
..   - Added
..   - Introduced
..   - Deprecated
..  - Removed
..   - Fixed

.. commented out the above listing so that it can remain as a guide of terms to use consistently for all relnotes
.. these comments must stay at the bottom of this section, else the relnotes don't render properly
.. values of "Improved, Updated, Added, Introduced, Deprecated, Removed, Fixed" to be used as entries for all release notes

**Introduced**

- Support for automation ees. All automation now runs in execution environments via containers, either directly via OpenShift, or locally via podman
- New PatternFly 4 based user-interface for increased performance, security, and consistency with other aap components

**Added**

- Added identity provider support for GitHub Enterprise
- Support for RHEL system crypto profiles to nginx configuration
- The ability to disable local system users and only pull users from configured identity providers
- Additional Prometheus metrics for tracking job event processing performance
- New ``awx-manage`` command for dumping host automation information
- Ability to set server-side password policies using Django's ``AUTH_PASSWORD_VALIDATORS`` setting
- Support for Centrify Vault as a credential lookup plugin
- Support for namespaces in Hashicorp Vault credential plugin

**Updated**

- OpenShift deployment to be done via an Operator instead of a playbook
- Python used by application to Python 3.8
- Nginx used to version 1.18
- PostgreSQL used to PostgreSQL 12, and moved to partitioned databases for performance
- The “container groups” feature to general availability from Tech Preview; now fully utilizes execution environments
- Inventory source, credential, and Ansible content collection to reference `controller` instead of `tower`

**Deprecated**

- None

**Removed**

- Support for isolated nodes
- Support for deploying on CentOS any version and RHEL 7
- Support for Mercurial projects
- Support for custom inventory scripts stored in controller use ``awx-manage export_custom_scripts`` to export them
- Resource profiling code ``AWX_RESOURCE_PROFILING_*``
- Support for custom Python virtual environments for execution. Use new ``awx-manage`` tools for assisting in migration
- Top-level /api/v2/job_events/ API endpoint
- The ability to disable job isolation
