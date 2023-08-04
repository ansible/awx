.. _licenses_feat_support:

Red Hat Ansible Automation Platform Controller Licensing, Updates, and Support
------------------------------------------------------------------------------

.. index::
   single: license

|RHAT| ("**Automation Controller**") is a software product provided as part of an annual |rhaap| subscription entered into between you and Red Hat, Inc. ("**Red Hat**").
 
Ansible is an open source software project and is licensed under the GNU General Public License version 3, as detailed in the Ansible source code: https://github.com/ansible/ansible/blob/devel/COPYING

You **must** have valid subscriptions attached before installing the |aap|. See :ref:`attach_subscriptions` for detail.

Support
==========

.. index::
    single: support

Red Hat offers support to paid |rhaap| customers.

If you or your company has purchased a subscription for |aap|, you can contact the support team at https://access.redhat.com. To better understand the levels of support which match your |aap| subscription, refer to :ref:`subscription-types`.
For details of what is covered under an |aap| subscription, please see the Scopes of Support at: https://access.redhat.com/support/policy/updates/ansible-tower#scope-of-coverage-4 and https://access.redhat.com/support/policy/updates/ansible-engine.

.. _trial-licenses:

Trial / Evaluation
=====================

.. index::
   single: license; trial
   single: evaluation
   single: trial


While a license is required for |at| to run, there is no fee for a trial license.

- Trial licenses for |rhaa| are available at: http://ansible.com/license 
- Support is not included in a trial license or during an evaluation of the |at| software.


.. _subscription-types:

Subscription Types
=======================

.. index:: 
   single: updates
   single: support
   single: license; types


|rhaap| is provided at various levels of support and number of machines as an annual Subscription. 

- Standard
   - Manage any size environment
   - Enterprise 8x5 support and SLA
   - Maintenance and upgrades included
   - Review the SLA at: https://access.redhat.com/support/offerings/production/sla
   - Review the Red Hat Support Severity Level Definitions at: https://access.redhat.com/support/policy/severity

- Premium
   - Manage any size environment, including mission-critical environments
   - Premium 24x7 support and SLA
   - Maintenance and upgrades included
   - Review the SLA at: https://access.redhat.com/support/offerings/production/sla
   - Review the Red Hat Support Severity Level Definitions at: https://access.redhat.com/support/policy/severity

All Subscription levels include regular updates and releases of |at|, Ansible, and any other components of the Platform.

For more information, contact Ansible via the Red Hat Customer portal at https://access.redhat.com/ or at http://www.ansible.com/contact-us/.


Node Counting in Licenses
=========================
.. index::
   single: license; nodes

The |RHAT| license defines the number of Managed Nodes that can be managed as part of a |rhaap| subscription. A typical license will say ‘License Count: 500’, which sets the maximum number of Managed Nodes at 500.

For more information on managed node requirements for licensing, please see https://access.redhat.com/articles/3331481.

.. note::

  At this time, Ansible does not recycle node counts or reset automated hosts.


.. _attach_subscriptions:

Attaching Subscriptions
=========================
.. index::
   pair: subscription; attaching
   pair: subscription; consume   

You **must** have valid subscriptions attached before installing the |aap|. Attaching an |aap| subscription enables |ah| repositories. A valid subscription needs to be attached to the |ah| node only. Other nodes do not need to have a valid subscription/pool attached, even if the **[automationhub]** group is blank, given this is done at the ``repos_el`` role level and that this role is run on both **[default]** and **[automationhub]** hosts. 

.. note::

  Attaching subscriptions is unnecessary if your Red Hat account enabled `Simple Content Access Mode <https://access.redhat.com/articles/simple-content-access>`_. But you still need to register to RHSM or Satellite before installing the |aap|.

To find out the ``pool_id`` of your |aap| subscription:

::

    #subscription-manager list --available --all | grep "Ansible Automation Platform" -B 3 -A 6

The command returns the following:

::

  Subscription Name: Red Hat Ansible Automation Platform, Premium (5000 Managed Nodes)
  Provides: Red Hat Ansible Engine
  Red Hat Single Sign-On
  Red Hat Ansible Automation Platform
  SKU: MCT3695
  Contract: ********
  Pool ID: ********************
  Provides Management: No
  Available: 4999
  Suggested: 1

To attach this subscription:

::

  #subscription-manager attach --pool=<pool_id>

If this is properly done, and all nodes have |rhaap| attached, then it will find the |ah| repositories correctly.

To check whether the subscription was successfully attached:

::

  #subscription-manager list --consumed


To remove this subscription:

::

  #subscription-manager remove --pool=<pool_id>


|AAP| Component Licenses
==============================

.. index::
    pair: licenses; components
    pair: licenses; RPM files
    pair: licenses; DEB files
    pair: licenses; installation bundle

To view the license information for the components included within |at|, refer to ``/usr/share/doc/automation-controller-<version>/README`` where ``<version>`` refers to the version of |at| you have installed.

To view a specific license, refer to ``/usr/share/doc/automation-controller-<version>/*.txt``, where ``*`` is replaced by the license file name to which you are referring. 

