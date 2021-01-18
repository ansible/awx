import { t } from '@lingui/macro';

import ActivityStream from './screens/ActivityStream';
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
import WorkflowApprovals from './screens/WorkflowApproval';

// Ideally, this should just be a regular object that we export, but we
// need the i18n. When lingui3 arrives, we will be able to import i18n
// directly and we can replace this function with a simple export.

export function verifyUserRole(user) {
  if (!(user.isSuperUser || user.isSystemAuditor)) {
    if (user.isOrgAdmin) {
      return `isVisibleOrgAdmin`;
    }

    if (!user.isOrgAdmin && user.isNotifAdmin) {
      return `isVisibleNotifAdmin`;
    }

    if (!user.isOrgAdmin && !user.isNotifAdmin) {
      return `isVisibleNormalUser`;
    }
  }
  return `isSuperUser`;
}

function getRouteConfig(i18n, user) {
  const sidebar = [
    {
      groupTitle: i18n._(t`Views`),
      groupId: 'views_group',
      routes: [
        {
          title: i18n._(t`Dashboard`),
          path: '/home',
          screen: Dashboard,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Jobs`),
          path: '/jobs',
          screen: Jobs,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Schedules`),
          path: '/schedules',
          screen: Schedules,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Activity Stream`),
          path: '/activity_stream',
          screen: ActivityStream,
        },
        {
          title: i18n._(t`Workflow Approvals`),
          path: '/workflow_approvals',
          screen: WorkflowApprovals,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
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
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Credentials`),
          path: '/credentials',
          screen: Credentials,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Projects`),
          path: '/projects',
          screen: Projects,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Inventories`),
          path: '/inventories',
          screen: Inventory,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Hosts`),
          path: '/hosts',
          screen: Hosts,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
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
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Users`),
          path: '/users',
          screen: Users,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Teams`),
          path: '/teams',
          screen: Teams,
          isVisibleNormalUser: true,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
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
          isVisibleNormalUser: false,
          isVisibleOrgAdmin: false,
          isVisibleNotifAdmin: false,
        },
        {
          title: i18n._(t`Notifications`),
          path: '/notification_templates',
          screen: NotificationTemplates,
          isVisibleNormalUser: false,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: true,
        },
        {
          title: i18n._(t`Management Jobs`),
          path: '/management_jobs',
          screen: ManagementJobs,
          isVisibleNormalUser: false,
          isVisibleOrgAdmin: false,
          isVisibleNotifAdmin: false,
        },
        {
          title: i18n._(t`Instance Groups`),
          path: '/instance_groups',
          screen: InstanceGroups,
          isVisibleNormalUser: false,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: false,
        },
        {
          title: i18n._(t`Applications`),
          path: '/applications',
          screen: Applications,
          isVisibleNormalUser: false,
          isVisibleOrgAdmin: true,
          isVisibleNotifAdmin: false,
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
          isVisibleNormalUser: false,
          isVisibleOrgAdmin: false,
          isVisibleNotifAdmin: false,
        },
      ],
    },
  ];

  const filterRoutes = (groupTitle, groupId, routes, filter) => {
    const filteredRoutes = routes.filter(item => item[filter] === true);

    if (filteredRoutes.length > 0) {
      return { groupTitle, groupId, routes: filteredRoutes };
    }
    return undefined;
  };

  let userRole = '';

  userRole = verifyUserRole(user);

  if (userRole !== `isSuperUser`) {
    const modifiedSideBar = [];

    sidebar.forEach(({ groupTitle, groupId, routes }) => {
      const filteredSideBar = filterRoutes(
        groupTitle,
        groupId,
        routes,
        userRole
      );
      if (filteredSideBar !== undefined) {
        modifiedSideBar.push(filteredSideBar);
      }
    });

    return modifiedSideBar;
  }
  return sidebar;
}

export default getRouteConfig;
