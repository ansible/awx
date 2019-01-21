import React from 'react';
import { Route, Switch } from 'react-router-dom';

import OrganizationsList from './screens/OrganizationsList';
import OrganizationAdd from './screens/OrganizationAdd';
import Organization from './screens/Organization/Organization';

export default ({ api, match, history }) => (
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
        <Organization
          api={api}
          history={history}
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
