import React from 'react';
import { Route, Switch } from 'react-router-dom';

import OrganizationAdd from './views/Organization.add';
import OrganizationView from './views/Organization.view';
import OrganizationsList from './views/Organizations.list';

export default ({ api, match }) => (
  <Switch>
    <Route
      path={`${match.path}/add`}
      render={() => (
        <OrganizationAdd
          api={api}
        />
      )}
    />
    <Route
      path={`${match.path}/:id`}
      render={() => (
        <OrganizationView
          api={api}
        />
      )}
    />
    <Route
      path={`${match.path}`}
      render={() => (
        <OrganizationsList
          api={api}
        />
      )}
    />
  </Switch>
);
