import React from 'react';
import { Redirect, Route, Switch } from 'react-router-dom';
import InstanceList from './InstanceList';
import InstanceDetails from '../InstanceDetails';

function Instances({ setBreadcrumb, instanceGroup }) {
  return (
    <Switch>
      <Redirect
        from="/instance_groups/:id/instances/:instanceId"
        to="/instance_groups/:id/instances/:instanceId/details"
        exact
      />
      <Route
        key="details"
        path="/instance_groups/:id/instances/:instanceId/details"
      >
        <InstanceDetails
          instanceGroup={instanceGroup}
          setBreadcrumb={setBreadcrumb}
        />
      </Route>
      <Route key="instanceList" path="/instance_groups/:id/instances">
        <InstanceList instanceGroup={instanceGroup} />
      </Route>
    </Switch>
  );
}

export default Instances;
