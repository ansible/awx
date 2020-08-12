import React from 'react';
import { Route } from 'react-router-dom';
import SmartInventoryHostList from './SmartInventoryHostList';
import { Inventory } from '../../../types';

function SmartInventoryHosts({ inventory }) {
  return (
    <Route key="host-list" path="/inventories/smart_inventory/:id/hosts">
      <SmartInventoryHostList inventory={inventory} />
    </Route>
  );
}

SmartInventoryHosts.propTypes = {
  inventory: Inventory.isRequired,
};

export default SmartInventoryHosts;
