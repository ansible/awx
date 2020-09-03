import { t } from '@lingui/macro';

import Applications from './screens/Application';
import Credentials from './screens/Credential';
import CredentialTypes from './screens/CredentialType';
import Dashboard from './screens/Dashboard';
import Hosts from './screens/Host';
import InstanceGroups from './screens/InstanceGroup';
import Inventory from './screens/Inventory';
import { Jobs } from './screens/Job';
import ManagementJobs from './screens/ManagementJob';
import NotificationTemplates from './screens/NotificationTemplate';
import Organizations from './screens/Organization';
import Projects from './screens/Project';
import Schedules from './screens/Schedule';
import Settings from './screens/Setting';
import Teams from './screens/Team';
import Templates from './screens/Template';
import Users from './screens/User';

// Ideally, this should just be a regular object that we export, but we
// need the i18n. When lingui3 arrives, we will be able to import i18n
// directly and we can replace this function with a simple export.

function getRouteConfig(i18n) {
  return [
    {
      groupTitle: i18n._(t`Views`),
      groupId: 'views_group',
      routes: [
        {
          title: i18n._(t`Dashboard`),
          path: '/home',
          screen: Dashboard,
        },
        {
          title: i18n._(t`Jobs`),
          path: '/jobs',
          screen: Jobs,
        },
        {
          title: i18n._(t`Schedules`),
          path: '/schedules',
          screen: Schedules,
        },
      ],
    },
    {
      groupTitle: i18n._(t`Resources`),
      groupId: 'resources_group',
      routes: [
        {
          title: i18n._(t`Templates`),
          path: '/templates',
          screen: Templates,
        },
        {
          title: i18n._(t`Credentials`),
          path: '/credentials',
          screen: Credentials,
        },
        {
          title: i18n._(t`Projects`),
          path: '/projects',
          screen: Projects,
        },
        {
          title: i18n._(t`Inventories`),
          path: '/inventories',
          screen: Inventory,
        },
        {
          title: i18n._(t`Hosts`),
          path: '/hosts',
          screen: Hosts,
        },
      ],
    },
    {
      groupTitle: i18n._(t`Access`),
      groupId: 'access_group',
      routes: [
        {
          title: i18n._(t`Organizations`),
          path: '/organizations',
          screen: Organizations,
        },
        {
          title: i18n._(t`Users`),
          path: '/users',
          screen: Users,
        },
        {
          title: i18n._(t`Teams`),
          path: '/teams',
          screen: Teams,
        },
      ],
    },
    {
      groupTitle: i18n._(t`Administration`),
      groupId: 'administration_group',
      routes: [
        {
          title: i18n._(t`Credential Types`),
          path: '/credential_types',
          screen: CredentialTypes,
        },
        {
          title: i18n._(t`Notifications`),
          path: '/notification_templates',
          screen: NotificationTemplates,
        },
        {
          title: i18n._(t`Management Jobs`),
          path: '/management_jobs',
          screen: ManagementJobs,
        },
        {
          title: i18n._(t`Instance Groups`),
          path: '/instance_groups',
          screen: InstanceGroups,
        },
        {
          title: i18n._(t`Applications`),
          path: '/applications',
          screen: Applications,
        },
      ],
    },
    {
      groupTitle: i18n._(t`Settings`),
      groupId: 'settings',
      routes: [
        {
          title: i18n._(t`Settings`),
          path: '/settings',
          screen: Settings,
        },
      ],
    },
  ];
}

export default getRouteConfig;
