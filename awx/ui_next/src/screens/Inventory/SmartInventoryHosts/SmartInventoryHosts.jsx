import React from 'react';
import { Route, Switch } from 'react-router-dom';
import SmartInventoryHostList from './SmartInventoryHostList';
import SmartInventoryHost from '../SmartInventoryHost';
import { Inventory } from '../../../types';

function SmartInventoryHosts({ inventory, setBreadcrumb }) {
  return (
    <Switch>
      <Route key="host" path="/inventories/smart_inventory/:id/hosts/:hostId">
        <SmartInventoryHost
          setBreadcrumb={setBreadcrumb}
          inventory={inventory}
        />
      </Route>
      <Route key="host-list" path="/inventories/smart_inventory/:id/hosts">
        <SmartInventoryHostList inventory={inventory} />
      </Route>
    </Switch>
  );
}

SmartInventoryHosts.propTypes = {
  inventory: Inventory.isRequired,
};

export default SmartInventoryHosts;
