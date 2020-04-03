import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route, withRouter } from 'react-router-dom';

import InventoryHostGroupsList from './InventoryHostGroupsList';

function InventoryHostGroups({ location, match }) {
  return (
    <Switch>
      <Route
        key="list"
        path="/inventories/inventory/:id/hosts/:hostId/groups"
        render={() => {
          return <InventoryHostGroupsList location={location} match={match} />;
        }}
      />
    </Switch>
  );
}

export { InventoryHostGroups as _InventoryHostGroups };
export default withI18n()(withRouter(InventoryHostGroups));
