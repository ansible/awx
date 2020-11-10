import React, { Fragment, useState, useCallback } from 'react';
import { Route, useRouteMatch, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import { Config } from '../../contexts/Config';

import UsersList from './UserList/UserList';
import UserAdd from './UserAdd/UserAdd';
import User from './User';

function Users({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/users': i18n._(t`Users`),
    '/users/add': i18n._(t`Create New User`),
  });
  const match = useRouteMatch();

  const addUserBreadcrumb = useCallback(
    (user, token) => {
      if (!user) {
        return;
      }

      setBreadcrumbConfig({
        '/users': i18n._(t`Users`),
        '/users/add': i18n._(t`Create New User`),
        [`/users/${user.id}`]: `${user.username}`,
        [`/users/${user.id}/edit`]: i18n._(t`Edit Details`),
        [`/users/${user.id}/details`]: i18n._(t`Details`),
        [`/users/${user.id}/roles`]: i18n._(t`Roles`),
        [`/users/${user.id}/teams`]: i18n._(t`Teams`),
        [`/users/${user.id}/organizations`]: i18n._(t`Organizations`),
        [`/users/${user.id}/tokens`]: i18n._(t`Tokens`),
        [`/users/${user.id}/tokens/add`]: i18n._(t`Create user token`),
        [`/users/${user.id}/tokens/${token && token.id}`]: i18n._(
          t`Application Name`
        ),
        [`/users/${user.id}/tokens/${token && token.id}/details`]: i18n._(
          t`Details`
        ),
      });
    },
    [i18n]
  );
  return (
    <Fragment>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path={`${match.path}/add`}>
          <UserAdd />
        </Route>
        <Route path={`${match.path}/:id`}>
          <Config>
            {({ me }) => (
              <User setBreadcrumb={addUserBreadcrumb} me={me || {}} />
            )}
          </Config>
        </Route>
        <Route path={`${match.path}`}>
          <UsersList />
        </Route>
      </Switch>
    </Fragment>
  );
}

export { Users as _Users };
export default withI18n()(Users);
