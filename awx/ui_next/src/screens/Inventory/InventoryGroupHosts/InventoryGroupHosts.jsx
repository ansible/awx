import React from 'react';
import { Switch, Route } from 'react-router-dom';
import InventoryGroupHostAdd from '../InventoryGroupHostAdd';
import InventoryGroupHostList from './InventoryGroupHostList';

function InventoryGroupHosts({ inventoryGroup }) {
  return (
    <Switch>
      <Route path="/inventories/inventory/:id/groups/:groupId/nested_hosts/add">
        <InventoryGroupHostAdd inventoryGroup={inventoryGroup} />
      </Route>
      <Route path="/inventories/inventory/:id/groups/:groupId/nested_hosts">
        <InventoryGroupHostList />
      </Route>
    </Switch>
  );
}

export default InventoryGroupHosts;
