import React from 'react';
import { Route, Switch } from 'react-router-dom';

import OrganizationAdd from './views/Organization.add';
import OrganizationView from './views/Organization.view';
import OrganizationsList from './views/Organizations.list';

const Organizations = ({ match }) => (
  <Switch>
    <Route path={`${match.path}/add`} component={OrganizationAdd} />
    <Route path={`${match.path}/:id`} component={OrganizationView} />
    <Route path={`${match.path}`} component={OrganizationsList} />
  </Switch>
);

export default Organizations;
