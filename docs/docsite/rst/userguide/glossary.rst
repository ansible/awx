Glossary
========

.. index::
   single: glossary

.. glossary::

    Ad Hoc
        Refers to running Ansible to perform some quick command, using /usr/bin/ansible, rather than the orchestration language, which is /usr/bin/ansible-playbook. An example of an ad hoc command might be rebooting 50 machines in your infrastructure. Anything you can do ad hoc can be accomplished by writing a Playbook, and Playbooks can also glue lots of other operations together.

    Callback Plugin
        Refers to some user-written code that can intercept results from Ansible and do something with them. Some supplied examples in the GitHub project perform custom logging, send email, or even play sound effects.

    Control Groups
        Also known as '*cgroups*', a control group is a feature in the Linux kernel that allows resources to be grouped and allocated to run certain processes. In addition to assigning resources to processes, cgroups can also report actual resource usage by all processes running inside of the cgroup.

    Check Mode
        Refers to running Ansible with the ``--check`` option, which does not make any changes on the remote systems, but only outputs the changes that might occur if the command ran without this flag. This is analogous to so-called “dry run” modes in other systems, though the user should be warned that this does not take into account unexpected command failures or cascade effects (which is true of similar modes in other systems). Use this to get an idea of what might happen, but it is not a substitute for a good staging environment.

    Container Groups
            Container Groups are a type of Instance Group that specify a configuration for provisioning a pod in a Kubernetes or OpenShift cluster where a job is run. These pods are provisioned on-demand and exist only for the duration of the playbook run. 

    Credentials
        Authentication details that may be utilized by AWX to launch jobs against machines, to synchronize with inventory sources, and to import project content from a version control system.

    Credential Plugin
        Python code that contains definitions for an external credential type, its metadata fields, and the code needed for interacting with a secret management system.

    Distributed Job
        A job that consists of a job template, an inventory, and slice size. When executed, a distributed job slices each inventory into a number of “slice size” chunks, which are then used to run smaller job slices.

    External Credential Type
        A managed credential type for AWX used for authenticating with a secret management system.

    Facts
        Facts are simply things that are discovered about remote nodes. While they can be used in playbooks and templates just like variables, facts are things that are inferred, rather than set. Facts are automatically discovered when running plays by executing the internal setup module on the remote nodes. You never have to call the setup module explicitly, it just runs, but it can be disabled to save time if it is not needed. For the convenience of users who are switching from other configuration management systems, the fact module also pulls in facts from the ‘ohai’ and ‘facter’ tools if they are installed, which are fact libraries from Chef and Puppet, respectively.

    Forks
        Ansible and AWX talk to remote nodes in parallel and the level of parallelism can be set several ways--during the creation or editing of a Job Template, by passing ``--forks``, or by editing the default in a configuration file. The default is a very conservative 5 forks, though if you have a lot of RAM, you can easily set this to a value like 50 for increased parallelism.

    Group
        A set of hosts in Ansible that can be addressed as a set, of which many may exist within a single Inventory.

    Group Vars
        The ``group_vars/`` files are files that live in a directory alongside an inventory file, with an optional filename named after each group. This is a convenient place to put variables that will be provided to a given group, especially complex data structures, so that these variables do not have to be embedded in the inventory file or playbook.

    Handlers
        Handlers are just like regular tasks in an Ansible playbook (see Tasks), but are only run if the Task contains a “notify” directive and also indicates that it changed something. For example, if a config file is changed then the task referencing the config file templating operation may notify a service restart handler. This means services can be bounced only if they need to be restarted. Handlers can be used for things other than service restarts, but service restarts are the most common usage.

    Host
        A system managed by AWX, which may include a physical, virtual, cloud-based server, or other device. Typically an operating system instance. Hosts are contained in Inventory. Sometimes referred to as a "node".

    Host Specifier
        Each Play in Ansible maps a series of tasks (which define the role, purpose, or orders of a system) to a set of systems. This “hosts:” directive in each play is often called the hosts specifier. It may select one system, many systems, one or more groups, or even some hosts that are in one group and explicitly not in another.

    Instance Group
        A group that contains instances for use in a clustered environment. An instance group provides the ability to group instances based on policy.   

    Inventory
        A collection of hosts against which Jobs may be launched.

    Inventory Script
        A very simple program (or a complicated one) that looks up hosts, group membership for hosts, and variable information from an external resource--whether that be a SQL database, a CMDB solution, or something like LDAP. This concept was adapted from Puppet (where it is called an “External Nodes Classifier”) and works more or less exactly the same way.

    Inventory Source
        Information about a cloud or other script that should be merged into the current inventory group, resulting in the automatic population of Groups, Hosts, and variables about those groups and hosts.

    Job
        One of many background tasks launched by AWX, this is usually the instantiation of a Job Template; the launch of an Ansible playbook. Other types of jobs include inventory imports, project synchronizations from source control, or administrative cleanup actions.

    Job Detail
        The history of running a particular job, including its output and success/failure status.

    Job Slice
        See :term:`Distributed Job`.    

    Job Template
        The combination of an Ansible playbook and the set of parameters required to launch it.

    JSON
        Ansible and AWX use JSON for return data from remote modules. This allows modules to be written in any language, not just Python.

    Mesh
        Describes a network comprising of nodes. Communication between nodes is established at the transport layer by protocols such as TCP, UDP or Unix sockets. See also, :term:`node`.

    Metadata
        Information for locating a secret in the external system once authenticated. The uses provides this information when linking an external credential to a target credential field.
    
    Node
        A node corresponds to entries in the instance database model, or the ``/api/v2/instances/`` endpoint, and is a machine participating in the cluster / mesh. The unified jobs API reports ``awx_node`` and ``execution_node`` fields. The execution node is where the job runs, and AWX node interfaces between the job and server functions.

        +-----------+------------------------------------------------------------------------------------------------------+
        | Node Type | Description                                                                                          |
        +===========+======================================================================================================+
        | Control   | Nodes that run persistent |aap| services, and delegate jobs to hybrid and execution nodes            |
        +-----------+------------------------------------------------------------------------------------------------------+
        | Hybrid    | Nodes that run persistent |aap| services and execute jobs                                            |
        +-----------+------------------------------------------------------------------------------------------------------+
        | Hop       | Used for relaying across the mesh only                                                               |
        +-----------+------------------------------------------------------------------------------------------------------+
        | Execution | Nodes that run jobs delivered from control nodes (jobs submitted from the user's Ansible automation) |
        +-----------+------------------------------------------------------------------------------------------------------+

    Notification Template
        An instance of a notification type (Email, Slack, Webhook, etc.) with a name, description, and a defined configuration.

    Notification 
        A manifestation of the notification template; for example, when a job fails a notification is sent using the configuration defined by the notification template.

    Notify
        The act of a task registering a change event and informing a handler task that another action needs to be run at the end of the play. If a handler is notified by multiple tasks, it will still be run only once. Handlers are run in the order they are listed, not in the order that they are notified.

    Organization
        A logical collection of Users, Teams, Projects, and Inventories. The highest level in the AWX object hierarchy is the Organization.

    Organization Administrator
        An AWX user with the rights to modify the Organization's membership and settings, including making new users and projects within that organization. An organization admin can also grant permissions to other users within the organization.

    Permissions
        The set of privileges assigned to Users and Teams that provide the ability to read, modify, and administer Projects, Inventories, and other AWX objects.

    Plays
        A playbook is a list of plays. A play is minimally a mapping between a set of hosts selected by a host specifier (usually chosen by groups, but sometimes by hostname globs) and the tasks which run on those hosts to define the role that those systems will perform. There can be one or many plays in a playbook.

    Playbook
        An Ansible playbook. Refer to http://docs.ansible.com/ for more information.

    Policy
        Policies dictate how instance groups behave and how jobs are executed.

    Project
        A logical collection of Ansible playbooks, represented in AWX.

    Roles
        Roles are units of organization in Ansible and AWX. Assigning a role to a group of hosts (or a set of groups, or host patterns, etc.) implies that they should implement a specific behavior. A role may include applying certain variable values, certain tasks, and certain handlers--or just one or more of these things. Because of the file structure associated with a role, roles become redistributable units that allow you to share behavior among playbooks--or even with other users.

    Secret Management System
        A server or service for securely storing and controlling access to tokens, passwords, certificates, encryption keys, and other sensitive data.

    Schedule
        The calendar of dates and times for which a job should run automatically.

    Sliced Job
        See :term:`Distributed Job`.

    Source Credential
        An external credential that is linked to the field of a target credential.

    Sudo
        Ansible does not require root logins and, since it is daemonless, does not require root level daemons (which can be a security concern in sensitive environments). Ansible can log in and perform many operations wrapped in a ``sudo`` command, and can work with both password-less and password-based sudo. Some operations that do not normally work with ``sudo`` (like ``scp`` file transfer) can be achieved with Ansible’s *copy*, *template*, and *fetch* modules while running in ``sudo`` mode.

    Superuser
        An admin of the AWX server who has permission to edit any object in the system, whether associated to any organization. Superusers can create organizations and other superusers.

    Survey
        Questions asked by a job template at job launch time, configurable on the job template.

    Target Credential
        A non-external credential with an input field that is linked to an external credential.

    Team
        A sub-division of an Organization with associated Users, Projects, Credentials, and Permissions. Teams provide a means to implement role-based access control schemes and delegate responsibilities across Organizations.

    User
        An AWX operator with associated permissions and credentials.

    Webhook
        Webhooks allow communication and information sharing between apps. They are used to respond to commits pushed to SCMs and launch job templates or workflow templates.

    Workflow Job Template
        A set consisting of any combination of job templates, project syncs, and inventory syncs, linked together in order to execute them as a single unit.

    YAML
        Ansible and AWX use YAML to define playbook configuration languages and also variable files. YAML has a minimum of syntax, is very clean, and is easy for people to skim. It is a good data format for configuration files and humans, but is also machine readable. YAML is fairly popular in the dynamic language community and the format has libraries available for serialization in many languages (Python, Perl, Ruby, etc.).
