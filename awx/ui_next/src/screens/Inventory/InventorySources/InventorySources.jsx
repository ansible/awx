import React from 'react';
import { Switch, Route } from 'react-router-dom';

import InventorySourceList from './InventorySourceList';

function InventorySources() {
  return (
    <Switch>
      <Route path="/inventories/:inventoryType/:id/sources">
        <InventorySourceList />
      </Route>
    </Switch>
  );
}

export default InventorySources;
