import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route } from 'react-router-dom';

import HostGroupsList from './HostGroupsList';

function HostGroups({ host }) {
  return (
    <Switch>
      <Route
        key="list"
        path="/hosts/:id/groups"
        render={() => {
          return <HostGroupsList host={host} />;
        }}
      />
    </Switch>
  );
}

export { HostGroups as _HostGroups };
export default withI18n()(HostGroups);
