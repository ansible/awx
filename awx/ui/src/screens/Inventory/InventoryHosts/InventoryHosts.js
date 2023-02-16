import React from 'react';
import { Switch, Route } from 'react-router-dom';

import InventoryHost from '../InventoryHost';
import InventoryHostAdd from '../InventoryHostAdd';
import InventoryHostList from './InventoryHostList';

function InventoryHosts({ setBreadcrumb, inventory }) {
  return (
    <Switch>
      <Route key="host-add" path="/inventories/:inventoryType/:id/hosts/add">
        <InventoryHostAdd inventory={inventory} />
      </Route>
      <Route key="host" path="/inventories/:inventoryType/:id/hosts/:hostId">
        <InventoryHost setBreadcrumb={setBreadcrumb} inventory={inventory} />
      </Route>
      <Route key="host-list" path="/inventories/:inventoryType/:id/hosts">
        <InventoryHostList inventory={inventory} />
      </Route>
    </Switch>
  );
}

export default InventoryHosts;
