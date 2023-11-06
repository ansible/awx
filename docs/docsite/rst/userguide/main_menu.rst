.. _ug_ui_main:

The User Interface
======================

.. index::
   pair: main menu; dashboard


The User Interface offers a friendly graphical framework for your IT orchestration needs. The left navigation bar provides quick access to resources, such as **Projects**, **Inventories**, **Job Templates**, and **Jobs**.

.. note::

  The new AWX User Interface is available for tech preview and is subject to change in a future release. To preview the new UI, click the **Enable Preview of New User Interface** toggle to **On** from the Miscellaneous System option of the Settings menu. 

  .. image:: ../common/images/configure-awx-system-misc-preview-newui.png
     :alt: Enabling preview of new user interface in the Miscellaneous System option of the Settings menu.

  After saving, logout and log back in to access the new UI from the preview banner. To return to the current UI, click the link on the top banner where indicated.

  .. image:: ../common/images/ug-dashboard-preview-banner.png
     :alt: Tech preview banner to view the new user interface.

Across the top-right side of the interface, you can access your user profile, the About page, view related documentation, and log out. Right below these options, you can view the activity stream for that user by clicking on the Activity Stream |activitystream| button. 

.. |activitystream| image:: ../common/images/activitystream.png
   :alt: Activity stream icon.

.. image:: ../common/images/ug-dashboard-top-nav.png
   :alt: Main screen with arrow showing where the activity stream icon resides on the Dashboard.




Views
-------

.. index::
   single: dashboard
   pair: views; jobs
   pair: views; schedule   

The User Interface provides several options for viewing information. 

.. contents::
    :local:


Dashboard view
~~~~~~~~~~~~~~~

.. index:: 
   pair: dashboard; job status
   pair: dashboard; jobs tab
   pair: dashboard; schedule status
   pair: dashboard; host count

   

The **Dashboard** view begins with a summary of your hosts, inventories, and projects. Each of these is linked to the corresponding objects for easy access.

.. image:: ../common/images/ug-dashboard-topsummary.png
   :alt: Dashboard showing a summary of your hosts, inventories, and projects; and job run statuses.

On the main Dashboard screen, a summary appears listing your current **Job Status**. The **Job Status** graph displays the number of successful and failed jobs over a specified time period. You can choose to limit the job types that are viewed, and to change the time horizon of the graph.

Also available for view are summaries of **Recent Jobs** and **Recent Templates** on their respective tabs.

The **Recent Jobs** section displays which jobs were most recently run, their status, and time when they were run as well.

.. image:: ../common/images/ug-dashboard-recent-jobs.png
   :alt: Summary of the most recently used jobs

The **Recent Templates** section of this display shows a summary of the most recently used templates. You can also access this summary by clicking **Templates** from the left navigation bar.

.. image:: ../common/images/ug-dashboard-recent-templates.png
   :alt: Summary of the most recently used templates

.. note::

    Clicking on **Dashboard** from the left navigation bar or the AWX logo at any time returns you to the Dashboard. 


Jobs view
~~~~~~~~~~

Access the **Jobs** view by clicking **Jobs** from the left navigation bar. This view shows all the jobs that have ran, including projects, templates, management jobs, SCM updates, playbook runs, etc.

.. image:: ../common/images/ug-dashboard-jobs-view.png
   :alt: Jobs view showing jobs that have ran, including projects, templates, management jobs, SCM updates, playbook runs, etc.


Schedules view
~~~~~~~~~~~~~~~

Access the Schedules view by clicking **Schedules** from the left navigation bar. This view shows all the scheduled jobs that are configured.


.. image:: ../common/images/ug-dashboard-schedule-view.png
   :alt: Schedules view showing all the scheduled jobs that are configured.


.. _ug_activitystreams:

Activity Stream
~~~~~~~~~~~~~~~~

.. index::
   single: activity stream


Most screens have an Activity Stream (|activitystream|) button. Clicking this brings up the
**Activity Stream** for this object.


|Users - Activity Stream|

.. |Users - Activity Stream| image:: ../common/images/users-activity-stream.png
   :alt: Summary of the recent activity on Activity Stream dashboard.

An Activity Stream shows all changes for a particular object. For each change, the Activity Stream shows the time of the event, the user that
initiated the event, and the action. The information displayed varies depending on the type of event. Clicking on the Examine (|examine|) button shows the event log for the change.

.. |examine| image:: ../common/images/examine-button.png
   :alt: Examine button

|event log|

.. |event log| image:: ../common/images/activity-stream-event-log.png
   :alt: Example of an event log of an Activity Stream instance.

The Activity Stream can be filtered by the initiating user (or the
system, if it was system initiated), and by any related object,
such as a particular credential, job template, or schedule.

The Activity Stream on the main Dashboard shows the Activity Stream for the entire instance. Most pages allow viewing an activity stream filtered for that specific object.


Workflow Approvals
~~~~~~~~~~~~~~~~~~~~

Access this view to see your workflow approval queue. The list contains actions that require you to approve or deny before a job can proceed. See  
:ref:`ug_wf_approval_nodes` for further detail.


Resources and Access
---------------------

The **Resources** and **Access** menus provide you access to the various components of AWX and allow you to configure who has permissions for those resources:

- Templates (:ref:`ug_JobTemplates` and :ref:`ug_wf_templates`)
- :ref:`ug_credentials`
- :ref:`ug_projects`
- :ref:`ug_inventories`
- :ref:`Hosts <ug_inventories_add_host>`
- :ref:`ug_organizations`
- :ref:`ug_users`
- :ref:`ug_teams`



Administration 
---------------

.. index::
   single: admin menu

The **Administration** menu provides access to the various administrative options. From here, you can create, view, and edit:

- :ref:`ug_credential_types` 
- :ref:`ug_notifications`
- :ref:`ag_management_jobs` 
- :ref:`ug_instance_groups`
- :ref:`Instances <ag_instances>`
- :ref:`ug_applications_auth`
- :ref:`ug_execution_environments`
- :ref:`ag_topology_viewer`


The Settings Menu
===================

Configuring global and system-level settings is accomplished through the **Settings** menu, which is described in further detail in the proceeding section. The **Settings** menu offers access to administrative configuration options.

.. include:: ../common/settings-menu.rst
