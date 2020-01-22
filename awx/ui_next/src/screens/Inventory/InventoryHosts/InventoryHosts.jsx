import React from 'react';
import { Switch, Route } from 'react-router-dom';

import Host from '../../Host/Host';
import InventoryHostList from './InventoryHostList';
import HostAdd from '../../Host/HostAdd';

function InventoryHosts({ setBreadcrumb, inventory }) {
  return (
    <Switch>
      <Route key="host-add" path="/inventories/inventory/:id/hosts/add">
        <HostAdd />
      </Route>
      <Route
        key="host"
        path="/inventories/inventory/:id/hosts/:hostId"
        render={() => (
          <Host setBreadcrumb={setBreadcrumb} inventory={inventory} />
        )}
      />
      <Route
        key="host-list"
        path="/inventories/inventory/:id/hosts/"
        render={() => <InventoryHostList setBreadcrumb={setBreadcrumb} />}
      />
    </Switch>
  );
}

export default InventoryHosts;
