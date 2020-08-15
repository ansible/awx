import React from 'react';
import { Route, Redirect, Switch } from 'react-router-dom';

import ExecutionEnvironmentDetails from './ExecutionEnvironmentDetails';
import ExecutionEnvironmentEdit from './ExecutionEnvironmentEdit';

function ExecutionEnvironment() {
  return (
    <Switch>
      <Redirect
        from="/execution_environments/:id"
        to="/execution_environments/:id/details"
        exact
      />
      <Route path="/execution_environments/:id/edit">
        <ExecutionEnvironmentEdit />
      </Route>
      <Route path="/execution_environments/:id/details">
        <ExecutionEnvironmentDetails />
      </Route>
    </Switch>
  );
}

export default ExecutionEnvironment;
