import React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';
import ApplicationEdit from '../ApplicationEdit';
import ApplicationDetails from '../ApplicationDetails';

function Application() {
  return (
    <>
      <Switch>
        <Redirect
          from="/applications/:id"
          to="/applications/:id/details"
          exact
        />
        <Route path="/applications/:id/edit">
          <ApplicationEdit />
        </Route>
        <Route path="/applications/:id/details">
          <ApplicationDetails />
        </Route>
      </Switch>
    </>
  );
}

export default Application;
