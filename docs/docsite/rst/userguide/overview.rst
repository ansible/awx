.. _overview:

Overview
========

.. index::
   pair: overview; features

Thank you for your interest in AWX. AWX makes it possible for users across an organization to share, vet, and manage automation content by means of a simple, powerful, and agentless technical implementation. IT managers can provide guidelines on how automation is applied to individual teams. Meanwhile, automation developers retain the freedom to write tasks that use existing knowledge, without the operational overhead of conforming to complex tools and frameworks. It is a more secure and stable foundation for deploying end-to-end automation solutions, from hybrid cloud to the edge. 

AWX allows users to define, operate, scale, and delegate automation across their organization.


Real-time Playbook Output and Exploration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; real-time playbook
   
Watch playbooks run in real time, seeing each host as they check in. Easily go back and explore the results for specific tasks and hosts in great detail. Search for specific plays or hosts and see just those results, or quickly zero in on errors that need to be corrected.

"Push Button" Automation
~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; automation

Access your favorite projects and re-trigger execution from the web interface with a minimum of clicking. AWX will ask for input variables, prompt for your credentials, kick off and monitor the job, and display results and host history over time.


Enhanced and Simplified Role-Based Access Control and Auditing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; role-based access control

AWX allows for the granting of permissions to perform a specific task (such as to view, create, or modify a file) to different teams or explicit users through role-based access control (RBAC). 

Keep some projects private, while allowing some users to edit inventory and others to run playbooks against only certain systems--either in check (dry run) or live mode. You can also allow certain users to use credentials without exposing the credentials to them. Regardless of what you do, AWX records the history of operations and who made them--including objects edited and jobs launched.

Based on user feedback, AWX both expands and simplifies its role-based access control. No longer is job template visibility configured via a combination of permissions on inventory, projects, and credentials. If you want to give any user or team permissions to use a job template, just assign permissions directly on the job template. Similarly, credentials are now full objects in AWX's RBAC system, and can be assigned to multiple users and/or teams for use.

AWX includes an ‘Auditor’ type, who can see all aspects of the systems automation, but has no permission to run or change automation, for those that need a system-level auditor. (This may also be useful for a service account that scrapes automation information from the REST API.) Refer to :ref:`rbac-ug` for more information.

Subsequent releases of AWX provides more granular permissions, making it easier to delegate inside your organizations and remove automation bottlenecks.


Cloud & Autoscaling Flexibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; autoscaling flexibility
   pair: features; cloud flexibility

AWX features a powerful provisioning callback feature that allows nodes to request configuration on demand. While optional, this is an ideal solution for a cloud auto-scaling scenario, integrating with provisioning servers like Cobbler, or when dealing with managed systems with unpredictable uptimes. Requiring no management software to be installed on remote nodes, the callback solution can be triggered via a simple call to 'curl' or 'wget', and is easily embeddable in init scripts, kickstarts, or preseeds. Access is controlled such that only machines in inventory can request configuration.


The Ideal RESTful API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; RESTful API

The AWX REST API is the ideal RESTful API for a systems management application, with all resources fully discoverable, paginated, searchable, and well modeled. A styled API browser allows API exploration from the API root at ``http://<server name>/api/``, showing off every resource and relation. Everything that can be done in the user interface can be done in the API - and more.

Backup and Restore
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; backup and restore

The ability to backup and restore your system(s) has been integrated into the AWX setup playbook, making it easy for you to backup and replicate your instance as needed.

Ansible Galaxy Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; Ansible Galaxy integration

When it comes to describing your automation, everyone repeats the DRY mantra--"Don’t Repeat Yourself." Using centralized copies of Ansible roles, such as in Ansible Galaxy, allows you to bring that philosophy to your playbooks. By including an Ansible Galaxy requirements.yml file in your project directory, AWX automatically fetches the roles your playbook needs from Galaxy, GitHub, or your local source control. Refer to :ref:`ug_galaxy` for more information. 

Inventory Support for OpenStack
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; OpenStack inventory support


Ansible is committed to making OpenStack simple for everyone to use. As part of that,  dynamic inventory support has been added for OpenStack. This allows you to easily target any of the virtual machines or images that you’re running in your OpenStack cloud.


Remote Command Execution
~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; remote command execution

Often times, you just need to do a simple task on a few hosts, whether it’s add a single user, update a single security vulnerability, or restart a misbehaving service. AWX includes remote command execution--any task that you can describe as a single Ansible play can be run on a host or group of hosts in your inventory, allowing you to get managing your systems quickly and easily. Plus, it is all backed by an RBAC engine and detailed audit logging, removing any questions regarding who has done what to what machines.


System Tracking
~~~~~~~~~~~~~~~~

.. index::
   pair: features; system tracking
   pair: features; fact cache


You can collect facts by using the fact caching feature. Refer to :ref:`ug_fact_caching` for more detail.


Integrated Notifications
~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; notifications

AWX allows you to easily keep track of the status of your automation. You can configure stackable notifications for job templates, projects, or entire organizations, and configure different notifications for job start, job success, job failure, and job approval (for workflow nodes). The following notification sources are supported:

- Email
- Grafana
- IRC
- Mattermost
- PagerDuty
- Rocket.Chat
- Slack
- Twilio
- Webhook (post to an arbitrary webhook, for integration into other tools)

Additionally, you can :ref:`customize notification messages <ug_custom_notifications>` for each of the above notification types.


Satellite Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; inventory sources, Red Hat Satellite 6

Dynamic inventory sources for Red Hat Satellite 6 are supported. 


Run-time Job Customization
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; run-time job customization

Bringing the flexibility of the Ansible command line, you can now prompt for any of the following:

- inventory
- credential
- job tags
- limits


Red Hat Insights Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; playbooks, Red Hat Insights

AWX supports integration with Red Hat Insights, which allows Insights playbooks to be used as a Project.


Enhanced User Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; UI
   pair: features; user interface

The layout of the user interface is organized with intuitive navigational elements. With information displayed at-a-glance, it is intuitive to find and use the automation you need. Compact and expanded viewing modes show and hide information as needed, and various built-in attributes make it easy to sort.


Custom Virtual Environments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; venv
   pair: features; custom environment

Custom Ansible environment support allows you to have different Ansible environments and specify custom paths for different teams and jobs.


Authentication Enhancements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; authentication
   pair: features; OAuth 2 token

AWX supports LDAP, SAML, token-based authentication. Enhanced LDAP and SAML support allows you to integrate your enterprise account information in a more flexible manner. Token-based Authentication allows for easily authentication of third-party tools and services with AWX via integrated OAuth 2 token support.

Cluster Management
~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; clustering
   pair: features; instance groups

Run-time management of cluster groups allows for easily configurable scaling.


Container Platform Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; container support

AWX is available as a containerized pod service for Kubernetes environments that can be scaled up and down easily as needed.


Workflow Enhancements
~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; workflows, inventory overrides
   pair: features; workflows, convergence nodes
   pair: features; workflows, nesting
   pair: features; workflows, approval
   pair: features; workflows, pause


In order to better model your complex provisioning, deployment, and orchestration workflows, AWX expanded workflows in a number
of ways:

- **Inventory overrides for Workflows**. You can now override an inventory across a workflow at workflow definition time, or even at launch time. Define your application deployment workflow, and then easily re-use them in multiple environments.

- **Convergence nodes for Workflows**. When modeling complex processes, you sometimes need to wait for multiple steps to finish before proceeding. Now AWX workflows can easily replicate this; workflow steps can now wait for any number of prior workflow steps to complete properly before proceeding.

- **Workflow Nesting**. Re-use individual workflows as components of a larger workflow. Examples include combining provisioning and application deployment workflows into a single master workflow.

- **Workflow Pause and Approval**. You can build workflows containing approval nodes that require user intervention. This makes it possible to pause workflows in between playbooks so that a user can give approval (or denial) for continuing on to the next step in the workflow.


Job Distribution
~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; jobs, slicing
   pair: features; jobs, distribution

As automation moves enterprise-wide, the need to automate at scale grows. AWX offer the ability to take a fact gathering or
configuration job running across thousands of machines and slice it into individual job slices that can be distributed across your AWX cluster for increased reliability, faster job completion, and better cluster utilization. If you need to change a parameter across 15,000 switches at
scale, or gather information across your multi-thousand-node RHEL estate, you can now do so easily.


Support for deployment in a FIPS-enabled environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; environment, FIPS


If you require running your environment in restricted modes such as FIPS, AWX deploys and runs in such environments.


Limit the number of hosts per organization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; limiting, hosts

Lots of large organizations have instances shared among many organizations. They do not want any one organization to be able to use all the licensed hosts, this feature allows superusers to set a specified upper limit on how many licensed hosts may be allocated to each organization. The AWX algorithm factors changes in the limit for an organization and the number of total hosts across all organizations. Any inventory updates will fail if an inventory sync brings an organization out of compliance with the policy. Additionally, superusers are able to 'over-allocate' their licenses, with a warning.


Inventory Plugins
~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; inventory plugins

Updated AWX to use the following inventory plugins from upstream collections if inventory updates are run with Ansible 2.9 and later:

- amazon.aws.aws_ec2
- community.vmware.vmware_vm_inventory
- azure.azcollection.azure_rm
- google.cloud.gcp_compute
- theforeman.foreman.foreman
- openstack.cloud.openstack
- ovirt.ovirt.ovirt
- awx.awx.tower


Secret Management System
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. index::
   pair: features; secret management system
   pair: features; credential plugins
   pair: features; credential management

With a secret management system, external credentials are stored and supplied for use in AWX so you don't have to provide them directly. 

