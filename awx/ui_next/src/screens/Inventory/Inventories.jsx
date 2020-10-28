import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import { InventoryList } from './InventoryList';
import Inventory from './Inventory';
import SmartInventory from './SmartInventory';
import InventoryAdd from './InventoryAdd';
import SmartInventoryAdd from './SmartInventoryAdd';

function Inventories({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/inventories': i18n._(t`Inventories`),
    '/inventories/inventory/add': i18n._(t`Create new inventory`),
    '/inventories/smart_inventory/add': i18n._(t`Create new smart inventory`),
  });

  const buildBreadcrumbConfig = useCallback(
    (inventory, nested, schedule) => {
      if (!inventory) {
        return;
      }

      const inventoryKind =
        inventory.kind === 'smart' ? 'smart_inventory' : 'inventory';

      const inventoryPath = `/inventories/${inventoryKind}/${inventory.id}`;
      const inventoryHostsPath = `${inventoryPath}/hosts`;
      const inventoryGroupsPath = `${inventoryPath}/groups`;
      const inventorySourcesPath = `${inventoryPath}/sources`;

      setBreadcrumbConfig({
        '/inventories': i18n._(t`Inventories`),
        '/inventories/inventory/add': i18n._(t`Create new inventory`),
        '/inventories/smart_inventory/add': i18n._(
          t`Create new smart inventory`
        ),

        [inventoryPath]: `${inventory.name}`,
        [`${inventoryPath}/access`]: i18n._(t`Access`),
        [`${inventoryPath}/completed_jobs`]: i18n._(t`Completed jobs`),
        [`${inventoryPath}/details`]: i18n._(t`Details`),
        [`${inventoryPath}/edit`]: i18n._(t`Edit details`),

        [inventoryHostsPath]: i18n._(t`Hosts`),
        [`${inventoryHostsPath}/add`]: i18n._(t`Create new host`),
        [`${inventoryHostsPath}/${nested?.id}`]: `${nested?.name}`,
        [`${inventoryHostsPath}/${nested?.id}/edit`]: i18n._(t`Edit details`),
        [`${inventoryHostsPath}/${nested?.id}/details`]: i18n._(
          t`Host details`
        ),
        [`${inventoryHostsPath}/${nested?.id}/completed_jobs`]: i18n._(
          t`Completed jobs`
        ),
        [`${inventoryHostsPath}/${nested?.id}/facts`]: i18n._(t`Facts`),
        [`${inventoryHostsPath}/${nested?.id}/groups`]: i18n._(t`Groups`),

        [inventoryGroupsPath]: i18n._(t`Groups`),
        [`${inventoryGroupsPath}/add`]: i18n._(t`Create new group`),
        [`${inventoryGroupsPath}/${nested?.id}`]: `${nested?.name}`,
        [`${inventoryGroupsPath}/${nested?.id}/edit`]: i18n._(t`Edit details`),
        [`${inventoryGroupsPath}/${nested?.id}/details`]: i18n._(
          t`Group details`
        ),
        [`${inventoryGroupsPath}/${nested?.id}/nested_hosts`]: i18n._(t`Hosts`),
        [`${inventoryGroupsPath}/${nested?.id}/nested_hosts/add`]: i18n._(
          t`Create new host`
        ),
        [`${inventoryGroupsPath}/${nested?.id}/nested_groups`]: i18n._(
          t`Groups`
        ),
        [`${inventoryGroupsPath}/${nested?.id}/nested_groups/add`]: i18n._(
          t`Create new group`
        ),

        [`${inventorySourcesPath}`]: i18n._(t`Sources`),
        [`${inventorySourcesPath}/add`]: i18n._(t`Create new source`),
        [`${inventorySourcesPath}/${nested?.id}`]: `${nested?.name}`,
        [`${inventorySourcesPath}/${nested?.id}/details`]: i18n._(t`Details`),
        [`${inventorySourcesPath}/${nested?.id}/edit`]: i18n._(t`Edit details`),
        [`${inventorySourcesPath}/${nested?.id}/schedules`]: i18n._(
          t`Schedules`
        ),
        [`${inventorySourcesPath}/${nested?.id}/schedules/${schedule?.id}`]: `${schedule?.name}`,
        [`${inventorySourcesPath}/${nested?.id}/schedules/${schedule?.id}/details`]: i18n._(
          t`Schedule details`
        ),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/inventories/inventory/add">
          <InventoryAdd />
        </Route>
        <Route path="/inventories/smart_inventory/add">
          <SmartInventoryAdd />
        </Route>
        <Route path="/inventories/inventory/:id">
          <Config>
            {({ me }) => (
              <Inventory setBreadcrumb={buildBreadcrumbConfig} me={me || {}} />
            )}
          </Config>
        </Route>
        <Route path="/inventories/smart_inventory/:id">
          <SmartInventory setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/inventories">
          <InventoryList />
        </Route>
      </Switch>
    </>
  );
}

export { Inventories as _Inventories };
export default withI18n()(Inventories);
