import React from 'react';
import { Switch, Route } from 'react-router-dom';
import InventoryRelatedGroupList from './InventoryRelatedGroupList';
import InventoryRelatedGroupAdd from '../InventoryRelatedGroupAdd';

function InventoryRelatedGroups() {
  return (
    <>
      <Switch>
        <Route
          key="addRelatedGroups"
          path="/inventories/inventory/:id/groups/:groupId/nested_groups/add"
        >
          <InventoryRelatedGroupAdd />
        </Route>
        <Route
          key="relatedGroups"
          path="/inventories/inventory/:id/groups/:groupId/nested_groups"
        >
          <InventoryRelatedGroupList />
        </Route>
      </Switch>
    </>
  );
}
export default InventoryRelatedGroups;
