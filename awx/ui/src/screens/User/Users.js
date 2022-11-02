import React, { useState, useCallback } from 'react';
import { Route, useRouteMatch, Switch } from 'react-router-dom';

import { t } from '@lingui/macro';

import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import { Config } from 'contexts/Config';
import UsersList from './UserList/UserList';
import UserAdd from './UserAdd/UserAdd';
import User from './User';

function Users() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/users': t`Users`,
    '/users/add': t`Create New User`,
  });
  const match = useRouteMatch();

  const addUserBreadcrumb = useCallback((user, token) => {
    if (!user) {
      return;
    }

    setBreadcrumbConfig({
      '/users': t`Users`,
      '/users/add': t`Create New User`,
      [`/users/${user.id}`]: `${user.username}`,
      [`/users/${user.id}/edit`]: t`Edit Details`,
      [`/users/${user.id}/details`]: t`Details`,
      [`/users/${user.id}/roles`]: t`Roles`,
      [`/users/${user.id}/teams`]: t`Teams`,
      [`/users/${user.id}/organizations`]: t`Organizations`,
      [`/users/${user.id}/tokens`]: t`Tokens`,
      [`/users/${user.id}/tokens/add`]: t`Create user token`,
      [`/users/${user.id}/tokens/${token && token.id}/details`]: t`Details`,
    });
  }, []);
  return (
    <>
      <ScreenHeader streamType="user" breadcrumbConfig={breadcrumbConfig} />
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
          <PersistentFilters pageKey="users">
            <UsersList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export { Users as _Users };
export default Users;
