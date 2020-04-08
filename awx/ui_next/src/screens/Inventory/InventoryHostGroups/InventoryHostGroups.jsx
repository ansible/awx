import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route } from 'react-router-dom';

import InventoryHostGroupsList from './InventoryHostGroupsList';

function InventoryHostGroups() {
  return (
    <Switch>
      <Route key="list" path="/inventories/inventory/:id/hosts/:hostId/groups">
        <InventoryHostGroupsList />
      </Route>
    </Switch>
  );
}

export { InventoryHostGroups as _InventoryHostGroups };
export default withI18n()(InventoryHostGroups);
