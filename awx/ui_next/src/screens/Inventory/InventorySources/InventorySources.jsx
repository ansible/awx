import React from 'react';
import { Switch, Route } from 'react-router-dom';
import { Config } from 'contexts/Config';
import InventorySource from '../InventorySource';
import InventorySourceAdd from '../InventorySourceAdd';
import InventorySourceList from './InventorySourceList';

function InventorySources({ inventory, setBreadcrumb }) {
  return (
    <Switch>
      <Route key="add" path="/inventories/inventory/:id/sources/add">
        <InventorySourceAdd inventory={inventory} />
      </Route>
      <Route path="/inventories/inventory/:id/sources/:sourceId">
        <Config>
          {({ me }) => (
            <InventorySource
              inventory={inventory}
              setBreadcrumb={setBreadcrumb}
              me={me || {}}
            />
          )}
        </Config>
      </Route>
      <Route path="/inventories/:inventoryType/:id/sources">
        <InventorySourceList />
      </Route>
    </Switch>
  );
}

export default InventorySources;
