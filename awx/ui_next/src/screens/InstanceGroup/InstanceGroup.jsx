import React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';

import InstanceGroupDetails from './InstanceGroupDetails';
import InstanceGroupEdit from './InstanceGroupEdit';

function InstanceGroup() {
  return (
    <Switch>
      <Redirect
        from="/instance_groups/:id"
        to="/instance_groups/:id/details"
        exact
      />
      <Route path="/instance_groups/:id/edit">
        <InstanceGroupEdit />
      </Route>
      <Route path="/instance_groups/:id/details">
        <InstanceGroupDetails />
      </Route>
    </Switch>
  );
}

export default InstanceGroup;
