import React from 'react';
import { Switch, Route } from 'react-router-dom';
import InventoryGroupHostList from './InventoryGroupHostList';

function InventoryGroupHosts() {
  return (
    <Switch>
      {/* Route to InventoryGroupHostAddForm */}
      <Route path="/inventories/inventory/:id/groups/:groupId/nested_hosts">
        <InventoryGroupHostList />
      </Route>
    </Switch>
  );
}

export default InventoryGroupHosts;
