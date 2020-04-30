import React from 'react';
import { Switch, Route } from 'react-router-dom';
import InventorySourceAdd from '../InventorySourceAdd';
import InventorySourceList from './InventorySourceList';

function InventorySources() {
  return (
    <Switch>
      <Route key="add" path="/inventories/inventory/:id/sources/add">
        <InventorySourceAdd />
      </Route>
      <Route path="/inventories/:inventoryType/:id/sources">
        <InventorySourceList />
      </Route>
    </Switch>
  );
}

export default InventorySources;
