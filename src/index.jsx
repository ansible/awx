import React from 'react';
import { render } from 'react-dom';

import App from './App';
import api from './api';

import '@patternfly/react-core/dist/styles/base.css';
import '@patternfly/patternfly-next/patternfly.css';

import './app.scss';
import './components/Pagination/styles.scss';
import './components/DataListToolbar/styles.scss';

import Applications from './pages/Applications';
import Credentials from './pages/Credentials';
import CredentialTypes from './pages/CredentialTypes';
import Dashboard from './pages/Dashboard';
import InstanceGroups from './pages/InstanceGroups';
import Inventories from './pages/Inventories';
import InventoryScripts from './pages/InventoryScripts';
import Jobs from './pages/Jobs';
import Login from './pages/Login';
import ManagementJobs from './pages/ManagementJobs';
import NotificationTemplates from './pages/NotificationTemplates';
import Organizations from './pages/Organizations';
import Portal from './pages/Portal';
import Projects from './pages/Projects';
import Schedules from './pages/Schedules';
import AuthSettings from './pages/AuthSettings';
import JobsSettings from './pages/JobsSettings';
import SystemSettings from './pages/SystemSettings';
import UISettings from './pages/UISettings';
import License from './pages/License';
import Teams from './pages/Teams';
import Templates from './pages/Templates';
import Users from './pages/Users';

const routeGroups = [
  {
    groupId: 'views_group',
    title: 'Views',
    routes: [
      {
        path: '/home',
        title: 'Dashboard',
        component: Dashboard
      },
      {
        path: '/jobs',
        title: 'Jobs',
        component: Jobs
      },
      {
        path: '/schedules',
        title: 'Schedules',
        component: Schedules
      },
      {
        path: '/portal',
        title: 'Portal Mode',
        component: Portal
      },
    ],
  },
  {
    groupId: 'resources_group',
    title: "Resources",
    routes: [
      {
        path: '/templates',
        title: 'Templates',
        component: Templates
      },
      {
        path: '/credentials',
        title: 'Credentials',
        component: Credentials
      },
      {
        path: '/projects',
        title: 'Projects',
        component: Projects
      },
      {
        path: '/inventories',
        title: 'Inventories',
        component: Inventories
      },
      {
        path: '/inventory_scripts',
        title: 'Inventory Scripts',
        component: InventoryScripts
      },
    ],
  },
  {
    groupId: 'access_group',
    title: 'Access',
    routes: [
      {
        path: '/organizations',
        title: 'Organizations',
        component: Organizations
      },
      {
        path: '/users',
        title: 'Users',
        component: Users
      },
      {
        path: '/teams',
        title: 'Teams',
        component: Teams
      },
    ],
  },
  {
    groupId: 'administration_group',
    title: 'Administration',
    routes: [
      {
        path: '/credential_types',
        title: 'Credential Types',
        component: CredentialTypes
      },
      {
        path: '/notification_templates',
        title: 'Notifications',
        component: NotificationTemplates
      },
      {
        path: '/management_jobs',
        title: 'Management Jobs',
        component: ManagementJobs
      },
      {
        path: '/instance_groups',
        title: 'Instance Groups',
        component: InstanceGroups
      },
      {
        path: '/applications',
        title: 'Integrations',
        component: Applications
      },
    ],
  },
  {
    groupId: 'settings_group',
    title: 'Settings',
    routes: [
      {
        path: '/auth_settings',
        title: 'Authentication',
        component: AuthSettings
      },
      {
        path: '/jobs_settings',
        title: 'Jobs',
        component: JobsSettings
      },
      {
        path: '/system_settings',
        title: 'System',
        component: SystemSettings
      },
      {
        path: '/ui_settings',
        title: 'User Interface',
        component: UISettings
      },
      {
        path: '/license',
        title: 'License',
        component: License
      },
    ],
  },
];


export async function main () {
  const el = document.getElementById('app');
  // fetch additional config from server
  const { data } = await api.getRoot();
  const { custom_logo, custom_login_info } = data;

  render(
    <App
      logo={custom_logo}
      loginInfo={custom_login_info}
      routeGroups={routeGroups}
    />, el);
};

export default main();
