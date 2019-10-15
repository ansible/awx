import React from 'react';
import ReactDOM from 'react-dom';
import { Route, Switch, Redirect } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';

import '@patternfly/react-core/dist/styles/base.css';
import './app.scss';

import { isAuthenticated } from '@util/auth';
import Background from '@components/Background';
import Applications from '@screens/Application';
import Credentials from '@screens/Credential';
import CredentialTypes from '@screens/CredentialType';
import Dashboard from '@screens/Dashboard';
import InstanceGroups from '@screens/InstanceGroup';
import Inventories from '@screens/Inventory';
import InventoryScripts from '@screens/InventoryScript';
import { Jobs } from '@screens/Job';
import Login from '@screens/Login';
import ManagementJobs from '@screens/ManagementJob';
import NotificationTemplates from '@screens/NotificationTemplate';
import Organizations from '@screens/Organization';
import Portal from '@screens/Portal';
import Projects from '@screens/Project';
import Schedules from '@screens/Schedule';
import AuthSettings from '@screens/AuthSetting';
import JobsSettings from '@screens/JobsSetting';
import SystemSettings from '@screens/SystemSetting';
import UISettings from '@screens/UISetting';
import License from '@screens/License';
import Teams from '@screens/Team';
import Templates from '@screens/Template';
import Users from '@screens/User';
import NotFound from '@screens/NotFound';

import App from './App';
import RootProvider from './RootProvider';
import { BrandName } from './variables';

// eslint-disable-next-line import/prefer-default-export
export function main(render) {
  const el = document.getElementById('app');
  document.title = `Ansible ${BrandName}`;

  const removeTrailingSlash = (
    <Route
      exact
      strict
      path="/*/"
      render={({
        history: {
          location: { pathname, search, hash },
        },
      }) => <Redirect to={`${pathname.slice(0, -1)}${search}${hash}`} />}
    />
  );

  const defaultRedirect = () => {
    if (isAuthenticated(document.cookie)) {
      return <Redirect to="/home" />;
    }
    return (
      <Switch>
        {removeTrailingSlash}
        <Route
          path="/login"
          render={() => <Login isAuthenticated={isAuthenticated} />}
        />
        <Redirect to="/login" />
      </Switch>
    );
  };

  return render(
    <RootProvider>
      <I18n>
        {({ i18n }) => (
          <Background>
            <Switch>
              {removeTrailingSlash}
              <Route path="/login" render={defaultRedirect} />
              <Route exact path="/" render={defaultRedirect} />
              <Route
                render={() => {
                  if (!isAuthenticated(document.cookie)) {
                    return <Redirect to="/login" />;
                  }
                  return (
                    <App
                      navLabel={i18n._(t`Primary Navigation`)}
                      routeGroups={[
                        {
                          groupTitle: i18n._(t`Views`),
                          groupId: 'views_group',
                          routes: [
                            {
                              title: i18n._(t`Dashboard`),
                              path: '/home',
                              component: Dashboard,
                            },
                            {
                              title: i18n._(t`Jobs`),
                              path: '/jobs',
                              component: Jobs,
                            },
                            {
                              title: i18n._(t`Schedules`),
                              path: '/schedules',
                              component: Schedules,
                            },
                            {
                              title: i18n._(t`My View`),
                              path: '/portal',
                              component: Portal,
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
                              component: Templates,
                            },
                            {
                              title: i18n._(t`Credentials`),
                              path: '/credentials',
                              component: Credentials,
                            },
                            {
                              title: i18n._(t`Projects`),
                              path: '/projects',
                              component: Projects,
                            },
                            {
                              title: i18n._(t`Inventories`),
                              path: '/inventories',
                              component: Inventories,
                            },
                            {
                              title: i18n._(t`Inventory Scripts`),
                              path: '/inventory_scripts',
                              component: InventoryScripts,
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
                              component: Organizations,
                            },
                            {
                              title: i18n._(t`Users`),
                              path: '/users',
                              component: Users,
                            },
                            {
                              title: i18n._(t`Teams`),
                              path: '/teams',
                              component: Teams,
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
                              component: CredentialTypes,
                            },
                            {
                              title: i18n._(t`Notifications`),
                              path: '/notification_templates',
                              component: NotificationTemplates,
                            },
                            {
                              title: i18n._(t`Management Jobs`),
                              path: '/management_jobs',
                              component: ManagementJobs,
                            },
                            {
                              title: i18n._(t`Instance Groups`),
                              path: '/instance_groups',
                              component: InstanceGroups,
                            },
                            {
                              title: i18n._(t`Integrations`),
                              path: '/applications',
                              component: Applications,
                            },
                          ],
                        },
                        {
                          groupTitle: i18n._(t`Settings`),
                          groupId: 'settings_group',
                          routes: [
                            {
                              title: i18n._(t`Authentication`),
                              path: '/auth_settings',
                              component: AuthSettings,
                            },
                            {
                              title: i18n._(t`Jobs`),
                              path: '/jobs_settings',
                              component: JobsSettings,
                            },
                            {
                              title: i18n._(t`System`),
                              path: '/system_settings',
                              component: SystemSettings,
                            },
                            {
                              title: i18n._(t`User Interface`),
                              path: '/ui_settings',
                              component: UISettings,
                            },
                            {
                              title: i18n._(t`License`),
                              path: '/license',
                              component: License,
                            },
                          ],
                        },
                      ]}
                      render={({ routeGroups }) => {
                        const routeList = routeGroups
                          .reduce(
                            (allRoutes, { routes }) => allRoutes.concat(routes),
                            []
                          )
                          .map(({ component: PageComponent, path }) => (
                            <Route
                              key={path}
                              path={path}
                              render={({ match }) => (
                                <PageComponent match={match} />
                              )}
                            />
                          ));
                        routeList.push(
                          <Route
                            key="not-found"
                            path="*"
                            component={NotFound}
                          />
                        );
                        return <Switch>{routeList}</Switch>;
                      }}
                    />
                  );
                }}
              />
            </Switch>
          </Background>
        )}
      </I18n>
    </RootProvider>,
    el || document.createElement('div')
  );
}

main(ReactDOM.render);
