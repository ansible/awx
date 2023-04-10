import React from 'react';
import { Route, Switch } from 'react-router-dom';
import { Inventory } from 'types';
import AdvancedInventoryHostList from './AdvancedInventoryHostList';
import AdvancedInventoryHost from '../AdvancedInventoryHost';

function AdvancedInventoryHosts({ inventory, setBreadcrumb }) {
  return (
    <Switch>
      <Route key="host" path="/inventories/:inventoryType/:id/hosts/:hostId">
        <AdvancedInventoryHost
          setBreadcrumb={setBreadcrumb}
          inventory={inventory}
        />
      </Route>
      <Route key="host-list" path="/inventories/:inventoryType/:id/hosts">
        <AdvancedInventoryHostList inventory={inventory} />
      </Route>
    </Switch>
  );
}

AdvancedInventoryHosts.propTypes = {
  inventory: Inventory.isRequired,
};

export default AdvancedInventoryHosts;
