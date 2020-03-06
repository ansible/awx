import React from 'react';
import { Switch, Route } from 'react-router-dom';

import InventoryHostAdd from '../InventoryHostAdd';
import InventoryHostList from './InventoryHostList';

function InventoryHosts({ setBreadcrumb, inventory }) {
  return (
    <Switch>
      <Route key="host-add" path="/inventories/inventory/:id/hosts/add">
        <InventoryHostAdd inventory={inventory} />
      </Route>
      <Route key="host-list" path="/inventories/inventory/:id/hosts">
        <InventoryHostList />
      </Route>
    </Switch>
  );
}

export default InventoryHosts;
