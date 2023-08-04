

Available subscriptions or a subscription manifest authorize the use of the automation controller. To obtain your automation controller subscription, you can either: 

1. Provide your Red Hat or Satellite username and password on the license page.
2. Obtain a subscriptions manifest from your Subscription Allocations page on the customer portal. See :ref:`obtain_sub_manifest` in the |atu| for more detail. 

If you **have** a |rhaap| subscription, use your Red Hat customer credentials when you launch the controller to access your subscription information (see instructions below).

If you **do not** have a |rhaap| subscription, you can request a trial subscription `here <https://www.redhat.com/en/technologies/management/ansible/try-it>`_ or click **Request Subscription** and follow the instructions to request one.

**Disconnected environments with Satellite** will be able to use the login flow on vm-based installations if they have configured subscription manager on the controller instance to connect to their Satellite instance. Recommended workarounds for disconnected environments **without Satellite** include [1] downloading a manifest from access.redhat.com in a connected environment, then uploading it to the disconnected controller instance, or [2] connecting to the Internet through a proxy server. 

.. note:: In order to use a disconnected environment, it is necessary to have a valid |at| entitlement attached to your Satellite organization's manifest. This can be confirmed by using ``hammer subscription list \--organization <org_name>``.

To understand what is supported with your subscription, see :ref:`licenses_feat_support` for more information. If you have issues with the subscription you have received, please contact your Sales Account Manager or Red Hat Customer Service at https://access.redhat.com/support/contact/customerService/.

When the controller launches for the first time, the Subscription screen automatically displays.

|no license|

.. |no license| image:: ../common/images/no-license.png

.. _upload_manifest:

1. By default, the option to retrieve and import your subscription is to upload a subscription manifest you generate from https://access.redhat.com/management/subscription_allocations. See :ref:`obtain_sub_manifest` for more detail. Once you have a subscription manifest, you can upload it by browsing to the location where the file is saved (the subscription manifest is the complete .zip file, not its component parts). 

.. note:: If the **Browse** button in the subscription manifest option is grayed-out, clear the username and password fields to enable the **Browse** button.

Alternatively, you can choose the option to enter your Red Hat customer credentials using your username and password. Use your Satellite username/password if your controller cluster nodes are registered to Satellite via Subscription Manager. Once you entered your credentials, click **Get Subscriptions**. 


2. The subscription metadata is then retrieved from the RHSM/Satellite API, or from the manifest provided.

 - If it is a subscription manifest, and multiple subscription counts were applied in a single installation, the controller will combine the counts but use the earliest expiration date as the expiry (at which point you will need to refresh your subscription). 
	
 - If you entered your credential information (username/password), the controller retrieves your configured subscription service. Then it prompts you to choose the subscription you want to run (the example below shows multiple subscriptions) and entitles the controller with that metadata. You can log in over time and retrieve new subscriptions if you have renewed. 

.. note:: When your subscription expires (you can check this in the Subscription details of the Subscription settings window), you will need to renew it in the controller by one of these two methods. 

.. image:: ../common/images/license-password-entered.png

If you encounter the following error message, you will need the proper permissions required for the Satellite user with which the controller admin uses to apply a subscription.

.. image:: ../common/images/tower-license-error-satellite-user.png

The Satellite username/password is used to query the Satellite API for existing subscriptions. From the Satellite API, the automation controller gets back some metadata about those subscriptions, then filter through to find valid subscriptions that you could apply, which are then displayed as valid subscription options in the UI.

The following Satellite roles grant proper access:

- Custom with ``view_subscriptions`` and ``view_organizations`` filter
- Viewer
- Administrator
- Organization Admin
- Manager

As the *Custom* role is the most restrictive of these, this is the recommend role to use for your controller integration. Refer to the `Satellite documentation <https://access.redhat.com/documentation/en-us/red_hat_satellite/6.8/html/administering_red_hat_satellite/chap-Red_Hat_Satellite-Administering_Red_Hat_Satellite-Users_and_Roles#sect-Red_Hat_Satellite-Administering_Red_Hat_Satellite-Users_and_Roles-Creating_and_Managing_Roles>`_ on managing users and roles for more detail.

.. note:: The System Administrator role is not equivalent to the Administrator user checkbox, and will not provide sufficient permissions to access the subscriptions API page.

3. Click **Next** to proceed to **Tracking and Insights**. Tracking and insights collect data to help Red Hat improve the product by delivering you a much better user experience. For more information about data collection, refer to :ref:`usability_data_collection`. This option is checked by default, but you may opt out of any of the following:

  -  **User analytics** collects data from the controller User Interface. 
  -  **Insights Analytics** provides a high level analysis of your automation with |at|, which is used to help you identify trends and anomalous use of the controller. For opt-in of |AA| to have any effect, your instance of |at| **must** be running on |rhel|. See instructions described in the :ref:`user_data_insights` section. If you select to opt-in for this option, the screen expands and prompts for a username and password to enable Insights, if applicable.

.. note::

	You may change your analytics data collection preferences at any time, as described in the :ref:`usability_data_collection` section.

4. After you have specified your tracking and insights preferences, click **Next** to proceed to the End User Agreement.

5. Review and check the **I agree to the End User License Agreement** checkbox and click **Submit**.

Once your subscription has been accepted, the controller briefly displays the subscription details and navigates you to the Dashboard of the |at| interface. For later reference, you can return to this screen by clicking **Settings** from the left navigation bar and select **Subscription settings** from the Subscription option. 

|license accepted|

.. |license accepted| image:: ../common/images/qs-licenseaccepted.png

.. _subscription_compliance:

Subscription compliance
------------------------

.. index::
   pair: subscriptions; compliance
   pair: subscriptions; host metrics


A status of |compliant| indicates your subscription is in compliance with the number of hosts you have automated within your subscription count. Otherwise, your status will show an *Out of Compliance* status, indicating you have exceeded the number of hosts in your subscription. 

.. |compliant| image:: ../common/images/qs-license-compliant.png

.. image:: ../common/images/qs-license-non-compliant.png

Even if a host is automated in multiple inventories, it will count against your subscription's alloted host count.

Compliance is computed as such:

::
	
	managed > manifest_limit	=> 	non-compliant
	managed =< manifest_limit	=> 	compliant

Where ``managed`` is unique managed hosts without deletions. And ``manifest_limit`` is the number of managed hosts in the subscription manifest.

Other important information displayed are:

- **Hosts automated**: Host count automated by the job, which consumes the license count
- **Hosts imported**: Host count considering unique host names across all inventory sources (does not impact hosts remaining)
- **Hosts remaining**: Total host count minus hosts automated
- **Hosts deleted**: Hosts that were deleted, freeing the license capacity
- **Active hosts previously deleted**: Number of hosts now active that were previously deleted

For demonstration purposes, suppose you have a subscription capacity of 10 hosts:

- Starting with 9 hosts, 2 hosts were added and 3 hosts were deleted, you now have 8 hosts (compliant)
- 3 hosts were automated again, now you have 11 hosts, which puts you over the subscription limit of 10 (non-compliant)
- If you were to delete host(s), be sure to refresh the subscription details to see the change in count and status

.. _host_metrics_ui:

Click **Host Metrics** from the left navigation menu to view the activity associated with hosts, such as those that have been automated and deleted. Each unique hostname is listed and sorted by the user's preference.

.. image:: ../common/images/ug-host-metrics.png

.. note::

  A scheduled task automatically updates these values on a weekly basis and deletes jobs with hosts that were last automated more than year ago. 
  
You can delete directly from the Host Metrics view the hosts you no longer want to use by selecting the desired host(s) and clicking **Delete**. These are soft-deleted, meaning their records are not removed, but are not being used and thereby not counted towards your subscription usage.

.. image:: ../common/images/ug-host-metrics-delete.png


Host metrics utilities
-----------------------

The controller provides a way to generate a CSV output of the host metric data and host metric summary through the Command Line Interface (CLI) and to soft delete hosts in bulk through the API.

awx-manage utility
^^^^^^^^^^^^^^^^^^

The existing ``awx-manage`` utility is expanded to support the following options:

::

	awx-manage host_metric --csv

This command produces host metric data, a host metrics summary file, and a cluster info file. To package all the files into a single tarball for ease of distribution and sharing:

::

	awx-manage host_metric --tarball


To specify the number of rows (``<n>``) to output to each file:

::

	awx-manage host_metric --tarball --rows_per_file <n>


.. image:: ../common/images/ug-host-metrics-awx-manage.png

This example specifies 5 rows per file and produces a tarball that contains a config file, the reports, and a host metrics summary file. You can access the tarball and extract it from your local file folder directory. 

.. image:: ../common/images/ug-host-metrics-awx-manage-files.png

Below is an example of a report produced with 5 rows a file:

.. image:: ../common/images/ug-host-metrics-awx-manage-file-example.png

Below is an example of a config file:

.. image:: ../common/images/ug-host-metrics-awx-manage-config.png

This JSON file is what gets sent to and consumed by |AA|.

The host metrics summary file is blank and is only used as a placeholder for this release.

.. this section is commented out and will not be displayed but kept here as a note to myself for future releases when the summary will actually contain something

	.. image:: ../common/images/ug-host-metrics-awx-manage-summary.png

	The summary contains unique host count showing how much capacity of the license is consumed in a given month. It reveals the number of hosts added (consuming more license capacity) and deleted (freeing the license capacity) in the associated month(s). 


API endpoint functions
^^^^^^^^^^^^^^^^^^^^^^^

The API lists only non-deleted records and are sortable by ``last_automation`` and ``used_in_inventories`` columns.

Alternative to the UI, you can use the host metric API endpoint, ``api/v2/host_metric`` to soft-delete hosts:

::

	api/v2/host_metric <n> DELETE

A monthly scheduled task automatically deletes jobs that uses hosts from the Host Metric table that were last automated more than year ago. 

