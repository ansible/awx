import React from 'react';
import { Route, Switch, Redirect } from 'react-router-dom';

import CredentialTypeDetails from './CredentialTypeDetails';
import CredentialTypeEdit from './CredentialTypeEdit';

function CredentialType() {
  return (
    <Switch>
      <Redirect
        from="/credential_types/:id"
        to="/credential_types/:id/details"
        exact
      />
      <Route path="/credential_types/:id/edit">
        <CredentialTypeEdit />
      </Route>
      <Route path="/credential_types/:id/details">
        <CredentialTypeDetails />
      </Route>
    </Switch>
  );
}

export default CredentialType;
