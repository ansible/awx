import React from 'react';

import { Switch, Route } from 'react-router-dom';
import HostGroupsList from './HostGroupsList';

function HostGroups({ host }) {
  return (
    <Switch>
      <Route key="list" path="/hosts/:id/groups">
        <HostGroupsList host={host} />
      </Route>
    </Switch>
  );
}

export { HostGroups as _HostGroups };
export default HostGroups;
