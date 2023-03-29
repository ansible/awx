import React, { useState, useCallback, useRef } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import { Config } from 'contexts/Config';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import { InventoryList } from './InventoryList';
import Inventory from './Inventory';
import SmartInventory from './SmartInventory';
import ConstructedInventory from './ConstructedInventory';
import InventoryAdd from './InventoryAdd';
import SmartInventoryAdd from './SmartInventoryAdd';
import ConstructedInventoryAdd from './ConstructedInventoryAdd';
import { getInventoryPath } from './shared/utils';

function Inventories() {
  const initScreenHeader = useRef({
    '/inventories': t`Inventories`,
    '/inventories/inventory/add': t`Create new inventory`,
    '/inventories/smart_inventory/add': t`Create new smart inventory`,
    '/inventories/constructed_inventory/add': t`Create new constructed inventory`,
  });

  const [breadcrumbConfig, setScreenHeader] = useState(
    initScreenHeader.current
  );

  const [inventory, setInventory] = useState();
  const [nestedObject, setNestedGroup] = useState();
  const [schedule, setSchedule] = useState();

  const setBreadcrumbConfig = useCallback(
    (passedInventory, passedNestedObject, passedSchedule) => {
      if (passedInventory && passedInventory.name !== inventory?.name) {
        setInventory(passedInventory);
      }
      if (
        passedNestedObject &&
        passedNestedObject.name !== nestedObject?.name
      ) {
        setNestedGroup(passedNestedObject);
      }
      if (passedSchedule && passedSchedule.name !== schedule?.name) {
        setSchedule(passedSchedule);
      }
      if (!inventory) {
        return;
      }

      const inventoryPath = getInventoryPath(inventory);
      const inventoryHostsPath = `${inventoryPath}/hosts`;
      const inventoryGroupsPath = `${inventoryPath}/groups`;
      const inventorySourcesPath = `${inventoryPath}/sources`;

      setScreenHeader({
        ...initScreenHeader.current,
        [inventoryPath]: `${inventory.name}`,
        [`${inventoryPath}/access`]: t`Access`,
        [`${inventoryPath}/jobs`]: t`Jobs`,
        [`${inventoryPath}/details`]: t`Details`,
        [`${inventoryPath}/job_templates`]: t`Job Templates`,
        [`${inventoryPath}/edit`]: t`Edit details`,

        [inventoryHostsPath]: t`Hosts`,
        [`${inventoryHostsPath}/add`]: t`Create new host`,
        [`${inventoryHostsPath}/${nestedObject?.id}`]: `${nestedObject?.name}`,
        [`${inventoryHostsPath}/${nestedObject?.id}/edit`]: t`Edit details`,
        [`${inventoryHostsPath}/${nestedObject?.id}/details`]: t`Host details`,
        [`${inventoryHostsPath}/${nestedObject?.id}/jobs`]: t`Jobs`,
        [`${inventoryHostsPath}/${nestedObject?.id}/facts`]: t`Facts`,
        [`${inventoryHostsPath}/${nestedObject?.id}/groups`]: t`Groups`,

        [inventoryGroupsPath]: t`Groups`,
        [`${inventoryGroupsPath}/add`]: t`Create new group`,
        [`${inventoryGroupsPath}/${nestedObject?.id}`]: `${nestedObject?.name}`,
        [`${inventoryGroupsPath}/${nestedObject?.id}/edit`]: t`Edit details`,
        [`${inventoryGroupsPath}/${nestedObject?.id}/details`]: t`Group details`,
        [`${inventoryGroupsPath}/${nestedObject?.id}/nested_hosts`]: t`Hosts`,
        [`${inventoryGroupsPath}/${nestedObject?.id}/nested_hosts/add`]: t`Create new host`,
        [`${inventoryGroupsPath}/${nestedObject?.id}/nested_groups`]: t`Related Groups`,
        [`${inventoryGroupsPath}/${nestedObject?.id}/nested_groups/add`]: t`Create new group`,

        [`${inventorySourcesPath}`]: t`Sources`,
        [`${inventorySourcesPath}/add`]: t`Create new source`,
        [`${inventorySourcesPath}/${nestedObject?.id}`]: `${nestedObject?.name}`,
        [`${inventorySourcesPath}/${nestedObject?.id}/details`]: t`Details`,
        [`${inventorySourcesPath}/${nestedObject?.id}/edit`]: t`Edit details`,
        [`${inventorySourcesPath}/${nestedObject?.id}/schedules`]: t`Schedules`,
        [`${inventorySourcesPath}/${nestedObject?.id}/schedules/${schedule?.id}`]: `${schedule?.name}`,
        [`${inventorySourcesPath}/${nestedObject?.id}/schedules/add`]: t`Create New Schedule`,
        [`${inventorySourcesPath}/${nestedObject?.id}/schedules/${schedule?.id}/details`]: t`Schedule details`,
        [`${inventorySourcesPath}/${nestedObject?.id}/notifications`]: t`Notifications`,
      });
    },
    [inventory, nestedObject, schedule]
  );

  return (
    <>
      <ScreenHeader
        streamType="inventory"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/inventories/inventory/add">
          <InventoryAdd />
        </Route>
        <Route path="/inventories/smart_inventory/add">
          <SmartInventoryAdd />
        </Route>
        <Route path="/inventories/constructed_inventory/add">
          <ConstructedInventoryAdd />
        </Route>
        <Route path="/inventories/inventory/:id">
          <Config>
            {({ me }) => (
              <Inventory setBreadcrumb={setBreadcrumbConfig} me={me || {}} />
            )}
          </Config>
        </Route>
        <Route path="/inventories/smart_inventory/:id">
          <SmartInventory setBreadcrumb={setBreadcrumbConfig} />
        </Route>
        <Route path="/inventories/constructed_inventory/:id">
          <ConstructedInventory setBreadcrumb={setBreadcrumbConfig} />
        </Route>
        <Route path="/inventories">
          <PersistentFilters pageKey="inventories">
            <InventoryList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export { Inventories as _Inventories };
export default Inventories;
