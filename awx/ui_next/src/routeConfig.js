import { t } from '@lingui/macro';

import ActivityStream from './screens/ActivityStream';
import Applications from './screens/Application';
import CredentialTypes from './screens/CredentialType';
import Credentials from './screens/Credential';
import Dashboard from './screens/Dashboard';
import ExecutionEnvironments from './screens/ExecutionEnvironment';
import Hosts from './screens/Host';
import InstanceGroups from './screens/InstanceGroup';
import Inventory from './screens/Inventory';
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
import { Jobs } from './screens/Job';

function getRouteConfig() {
  return [
    {
      groupTitle: t`Views`,
      groupId: 'views_group',
      routes: [
        {
          title: t`Dashboard`,
          path: '/home',
          screen: Dashboard,
        },
        {
          title: t`Jobs`,
          path: '/jobs',
          screen: Jobs,
        },
        {
          title: t`Schedules`,
          path: '/schedules',
          screen: Schedules,
        },
        {
          title: t`Activity Stream`,
          path: '/activity_stream',
          screen: ActivityStream,
        },
        {
          title: t`Workflow Approvals`,
          path: '/workflow_approvals',
          screen: WorkflowApprovals,
        },
      ],
    },
    {
      groupTitle: t`Resources`,
      groupId: 'resources_group',
      routes: [
        {
          title: t`Templates`,
          path: '/templates',
          screen: Templates,
        },
        {
          title: t`Credentials`,
          path: '/credentials',
          screen: Credentials,
        },
        {
          title: t`Projects`,
          path: '/projects',
          screen: Projects,
        },
        {
          title: t`Inventories`,
          path: '/inventories',
          screen: Inventory,
        },
        {
          title: t`Hosts`,
          path: '/hosts',
          screen: Hosts,
        },
      ],
    },
    {
      groupTitle: t`Access`,
      groupId: 'access_group',
      routes: [
        {
          title: t`Organizations`,
          path: '/organizations',
          screen: Organizations,
        },
        {
          title: t`Users`,
          path: '/users',
          screen: Users,
        },
        {
          title: t`Teams`,
          path: '/teams',
          screen: Teams,
        },
      ],
    },
    {
      groupTitle: t`Administration`,
      groupId: 'administration_group',
      routes: [
        {
          title: t`Credential Types`,
          path: '/credential_types',
          screen: CredentialTypes,
        },
        {
          title: t`Notifications`,
          path: '/notification_templates',
          screen: NotificationTemplates,
        },
        {
          title: t`Management Jobs`,
          path: '/management_jobs',
          screen: ManagementJobs,
        },
        {
          title: t`Instance Groups`,
          path: '/instance_groups',
          screen: InstanceGroups,
        },
        {
          title: t`Applications`,
          path: '/applications',
          screen: Applications,
        },
        {
          title: t`Execution Environments`,
          path: '/execution_environments',
          screen: ExecutionEnvironments,
        },
      ],
    },
    {
      groupTitle: t`Settings`,
      groupId: 'settings',
      routes: [
        {
          title: t`Settings`,
          path: '/settings',
          screen: Settings,
        },
      ],
    },
  ];
}

export default getRouteConfig;
