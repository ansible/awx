import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route } from 'react-router-dom';

import InventoryGroupAdd from '../InventoryGroupAdd/InventoryGroupAdd';

import InventoryGroup from '../InventoryGroup/InventoryGroup';
import InventoryGroupsList from './InventoryGroupsList';

function InventoryGroups({ setBreadcrumb, inventory }) {
  return (
    <Switch>
      <Route key="add" path="/inventories/inventory/:id/groups/add">
        <InventoryGroupAdd
          setBreadcrumb={setBreadcrumb}
          inventory={inventory}
        />
      </Route>
      <Route key="details" path="/inventories/inventory/:id/groups/:groupId/">
        <InventoryGroup inventory={inventory} setBreadcrumb={setBreadcrumb} />
      </Route>
      <Route key="list" path="/inventories/inventory/:id/groups">
        <InventoryGroupsList />
      </Route>
    </Switch>
  );
}

export { InventoryGroups as _InventoryGroups };
export default withI18n()(InventoryGroups);
