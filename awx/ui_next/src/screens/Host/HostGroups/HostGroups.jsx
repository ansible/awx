import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route, withRouter } from 'react-router-dom';

import HostGroupsList from './HostGroupsList';

function HostGroups({ location, match }) {
  return (
    <Switch>
      <Route
        key="list"
        path="/hosts/:id/groups"
        render={() => {
          return <HostGroupsList location={location} match={match} />;
        }}
      />
    </Switch>
  );
}

export { HostGroups as _HostGroups };
export default withI18n()(withRouter(HostGroups));
