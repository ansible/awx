.. _ag_configure_awx:

AWX Configuration
~~~~~~~~~~~~~~~~~~~

.. index::
   single: configure AWX

.. _configure_awx_overview:

You can configure various AWX settings within the Settings screen in the following tabs:

.. image:: ../common/images/ug-settings-menu-screen.png

Each tab contains fields with a **Reset** button, allowing you to revert any value entered back to the default value. **Reset All** allows you to revert all the values to their factory default values.

**Save** applies changes you make, but it does not exit the edit dialog. To return to the Settings screen, click **Settings** from the left navigation bar or use the breadcrumbs at the top of the current view.


Authentication
=================
.. index::
    single: social authentication
    single: authentication
    single: enterprise authentication
    pair: configuration; authentication

.. include:: ./configure_awx_authentication.rst


.. _configure_awx_jobs:

Jobs
=========
.. index::
   single: jobs
   pair: configuration; jobs

The Jobs tab allows you to configure the types of modules that are allowed to be used by AWX's Ad Hoc Commands feature, set limits on the number of jobs that can be scheduled, define their output size, and other details pertaining to working with Jobs in AWX.

1. From the left navigation bar, click **Settings** from the left navigation bar and select **Jobs settings** from the Settings screen.

2. Set the configurable options from the fields provided. Click the tooltip |help| icon next to the field that you need additional information or details about. Refer to the :ref:`ug_galaxy` section for details about configuring Galaxy settings.

.. note::

    The values for all the timeouts are in seconds.

.. image:: ../common/images/configure-awx-jobs.png

3. Click **Save** to apply the settings or **Cancel** to abandon the changes.


.. _configure_awx_system:

System
======
.. index::
   pair: configuration; system

The System tab allows you to define the base URL for the AWX host, configure alerts, enable activity capturing, control visibility of users, enable certain AWX features and functionality through a license file, and configure logging aggregation options.

1. From the left navigation bar, click **Settings**.

2. The right side of the Settings window is a set of configurable System settings. Select from the following options:

  - **Miscellaneous System settings**: enable activity streams, specify the default execution environment, define the base URL for the AWX host, enable AWX administration alerts, set user visibility, define analytics, specify usernames and passwords, and configure proxies.
  - **Miscellaneous Authentication settings**: configure options associated with authentication methods (built-in or SSO), sessions (timeout, number of sessions logged in, tokens), and social authentication mapping.
  - **Logging settings**: configure logging options based on the type you choose:

    .. image:: ../common/images/configure-awx-system-logging-types.png

    For more information about each of the logging aggregation types, refer to the :ref:`ag_logging` section of the |ata|.


3. Set the configurable options from the fields provided. Click the tooltip |help| icon next to the field that you need additional information or details about. Below is an example of the System settings window.

.. |help| image:: ../common/images/tooltips-icon.png

.. image:: ../common/images/configure-awx-system.png

.. note::

  The **Allow External Users to Create Oauth2 Tokens** setting is disabled by default. This ensures external users cannot *create* their own tokens. If you enable then disable it, any tokens created by external users in the meantime will still exist, and are not automatically revoked.

4. Click **Save** to apply the settings or **Cancel** to abandon the changes.

.. _configure_awx_ui:

User Interface
================
.. index::
   pair: configuration; UI
   pair: configuration; data collection
   pair: configuration; custom logo
   pair: configuration; custom login message
   pair: logo; custom
   pair: login message; custom

.. include:: ../common/logos_branding.rst
