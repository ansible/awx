import React from 'react';
import { Trans } from '@lingui/macro';

import ActivityStream from 'screens/ActivityStream';
import Applications from 'screens/Application';
import CredentialTypes from 'screens/CredentialType';
import Credentials from 'screens/Credential';
import Dashboard from 'screens/Dashboard';
import ExecutionEnvironments from 'screens/ExecutionEnvironment';
import Hosts from 'screens/Host';
import Instances from 'screens/Instances';
import InstanceGroups from 'screens/InstanceGroup';
import Inventory from 'screens/Inventory';
import ManagementJobs from 'screens/ManagementJob';
import NotificationTemplates from 'screens/NotificationTemplate';
import Organizations from 'screens/Organization';
import Projects from 'screens/Project';
import Schedules from 'screens/Schedule';
import Settings from 'screens/Setting';
import Teams from 'screens/Team';
import Templates from 'screens/Template';
import TopologyView from 'screens/TopologyView';
import Users from 'screens/User';
import WorkflowApprovals from 'screens/WorkflowApproval';
import { Jobs } from 'screens/Job';

function getRouteConfig(userProfile = {}) {
  let routeConfig = [
    {
      groupTitle: <Trans>Views</Trans>,
      groupId: 'views_group',
      routes: [
        {
          title: <Trans>Dashboard</Trans>,
          path: '/home',
          screen: Dashboard,
        },
        {
          title: <Trans>Jobs</Trans>,
          path: '/jobs',
          screen: Jobs,
        },
        {
          title: <Trans>Schedules</Trans>,
          path: '/schedules',
          screen: Schedules,
        },
        {
          title: <Trans>Activity Stream</Trans>,
          path: '/activity_stream',
          screen: ActivityStream,
        },
        {
          title: <Trans>Workflow Approvals</Trans>,
          path: '/workflow_approvals',
          screen: WorkflowApprovals,
        },
      ],
    },
    {
      groupTitle: <Trans>Resources</Trans>,
      groupId: 'resources_group',
      routes: [
        {
          title: <Trans>Templates</Trans>,
          path: '/templates',
          screen: Templates,
        },
        {
          title: <Trans>Credentials</Trans>,
          path: '/credentials',
          screen: Credentials,
        },
        {
          title: <Trans>Projects</Trans>,
          path: '/projects',
          screen: Projects,
        },
        {
          title: <Trans>Inventories</Trans>,
          path: '/inventories',
          screen: Inventory,
        },
        {
          title: <Trans>Hosts</Trans>,
          path: '/hosts',
          screen: Hosts,
        },
      ],
    },
    {
      groupTitle: <Trans>Access</Trans>,
      groupId: 'access_group',
      routes: [
        {
          title: <Trans>Organizations</Trans>,
          path: '/organizations',
          screen: Organizations,
        },
        {
          title: <Trans>Users</Trans>,
          path: '/users',
          screen: Users,
        },
        {
          title: <Trans>Teams</Trans>,
          path: '/teams',
          screen: Teams,
        },
      ],
    },
    {
      groupTitle: <Trans>Administration</Trans>,
      groupId: 'administration_group',
      routes: [
        {
          title: <Trans>Credential Types</Trans>,
          path: '/credential_types',
          screen: CredentialTypes,
        },
        {
          title: <Trans>Notifications</Trans>,
          path: '/notification_templates',
          screen: NotificationTemplates,
        },
        {
          title: <Trans>Management Jobs</Trans>,
          path: '/management_jobs',
          screen: ManagementJobs,
        },
        {
          title: <Trans>Instance Groups</Trans>,
          path: '/instance_groups',
          screen: InstanceGroups,
        },
        {
          title: <Trans>Instances</Trans>,
          path: '/instances',
          screen: Instances,
        },
        {
          title: <Trans>Applications</Trans>,
          path: '/applications',
          screen: Applications,
        },
        {
          title: <Trans>Execution Environments</Trans>,
          path: '/execution_environments',
          screen: ExecutionEnvironments,
        },
        {
          title: <Trans>Topology View</Trans>,
          path: '/topology_view',
          screen: TopologyView,
        },
      ],
    },
    {
      groupTitle: <Trans>Settings</Trans>,
      groupId: 'settings',
      routes: [
        {
          title: <Trans>Settings</Trans>,
          path: '/settings',
          screen: Settings,
        },
      ],
    },
  ];

  const deleteRoute = (name) => {
    routeConfig.forEach((group) => {
      group.routes = group.routes.filter(({ path }) => !path.includes(name));
    });
    routeConfig = routeConfig.filter((groups) => groups.routes.length);
  };

  const deleteRouteGroup = (name) => {
    routeConfig = routeConfig.filter(({ groupId }) => !groupId.includes(name));
  };

  if (userProfile?.isSuperUser || userProfile?.isSystemAuditor)
    return routeConfig;
  deleteRouteGroup('settings');
  deleteRoute('management_jobs');
  if (userProfile?.isOrgAdmin) return routeConfig;
  deleteRoute('instance_groups');
  deleteRoute('topology_view');
  if (!userProfile?.isNotificationAdmin) deleteRoute('notification_templates');

  return routeConfig;
}

export default getRouteConfig;
