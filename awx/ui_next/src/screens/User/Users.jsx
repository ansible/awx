import React, { Fragment, useState, useCallback } from 'react';
import { Route, useRouteMatch, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

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
    user => {
      if (!user) {
        return;
      }

      setBreadcrumbConfig({
        '/users': i18n._(t`Users`),
        '/users/add': i18n._(t`Create New User`),
        [`/users/${user.id}`]: `${user.username}`,
        [`/users/${user.id}/edit`]: i18n._(t`Edit Details`),
        [`/users/${user.id}/details`]: i18n._(t`Details`),
        [`/users/${user.id}/access`]: i18n._(t`Access`),
        [`/users/${user.id}/teams`]: i18n._(t`Teams`),
        [`/users/${user.id}/organizations`]: i18n._(t`Organizations`),
        [`/users/${user.id}/tokens`]: i18n._(t`Tokens`),
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
          <User setBreadcrumb={addUserBreadcrumb} />
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
