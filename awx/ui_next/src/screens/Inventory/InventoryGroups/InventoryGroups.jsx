import React from 'react';
import { withI18n } from '@lingui/react';

import { Switch, Route } from 'react-router-dom';

import InventoryGroupAdd from '../InventoryGroupAdd/InventoryGroupAdd';

import InventoryGroup from '../InventoryGroup/InventoryGroup';
import InventoryGroupsList from './InventoryGroupsList';

function InventoryGroups({ setBreadcrumb, inventory }) {
  return (
    <Switch>
      <Route
        key="add"
        path="/inventories/inventory/:id/groups/add"
        render={() => {
          return (
            <InventoryGroupAdd
              setBreadcrumb={setBreadcrumb}
              inventory={inventory}
            />
          );
        }}
      />
      <Route
        key="details"
        path="/inventories/inventory/:id/groups/:groupId/"
        render={() => (
          <InventoryGroup inventory={inventory} setBreadcrumb={setBreadcrumb} />
        )}
      />
      <Route
        key="list"
        path="/inventories/inventory/:id/groups"
        render={() => {
          return <InventoryGroupsList />;
        }}
      />
    </Switch>
  );
}

export { InventoryGroups as _InventoryGroups };
export default withI18n()(InventoryGroups);
