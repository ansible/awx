import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, withRouter, Switch } from 'react-router-dom';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';
import { InventoryList } from './InventoryList';
import Inventory from './Inventory';
import SmartInventory from './SmartInventory';
import InventoryAdd from './InventoryAdd';
import SmartInventoryAdd from './SmartInventoryAdd';

class Inventories extends Component {
  constructor(props) {
    super(props);
    const { i18n } = this.props;

    this.state = {
      breadcrumbConfig: {
        '/inventories': i18n._(t`Inventories`),
        '/inventories/inventory/add': i18n._(t`Create new inventory`),
        '/inventories/smart_inventory/add': i18n._(
          t`Create new smart inventory`
        ),
      },
    };
  }

  setBreadCrumbConfig = (inventory, nested) => {
    const { i18n } = this.props;
    if (!inventory) {
      return;
    }

    const inventoryKind =
      inventory.kind === 'smart' ? 'smart_inventory' : 'inventory';

    const inventoryPath = `/inventories/${inventoryKind}/${inventory.id}`;
    const inventoryHostsPath = `${inventoryPath}/hosts`;
    const inventoryGroupsPath = `${inventoryPath}/groups`;
    const inventorySourcesPath = `${inventoryPath}/sources`;

    const breadcrumbConfig = {
      '/inventories': i18n._(t`Inventories`),
      '/inventories/inventory/add': i18n._(t`Create new inventory`),
      '/inventories/smart_inventory/add': i18n._(t`Create new smart inventory`),

      [inventoryPath]: `${inventory.name}`,
      [`${inventoryPath}/access`]: i18n._(t`Access`),
      [`${inventoryPath}/completed_jobs`]: i18n._(t`Completed jobs`),
      [`${inventoryPath}/details`]: i18n._(t`Details`),
      [`${inventoryPath}/edit`]: i18n._(t`Edit details`),

      [inventoryHostsPath]: i18n._(t`Hosts`),
      [`${inventoryHostsPath}/add`]: i18n._(t`Create new host`),
      [`${inventoryHostsPath}/${nested?.id}`]: `${nested?.name}`,
      [`${inventoryHostsPath}/${nested?.id}/edit`]: i18n._(t`Edit details`),
      [`${inventoryHostsPath}/${nested?.id}/details`]: i18n._(t`Host Details`),
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

      [`${inventorySourcesPath}`]: i18n._(t`Sources`),
      [`${inventorySourcesPath}/add`]: i18n._(t`Create new source`),
      [`${inventorySourcesPath}/${nested?.id}`]: `${nested?.name}`,
      [`${inventorySourcesPath}/${nested?.id}/details`]: i18n._(t`Details`),
      [`${inventorySourcesPath}/${nested?.id}/edit`]: i18n._(t`Edit details`),
    };
    this.setState({ breadcrumbConfig });
  };

  render() {
    const { match, history, location } = this.props;
    const { breadcrumbConfig } = this.state;
    return (
      <>
        <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
        <Switch>
          <Route path={`${match.path}/inventory/add`}>
            <InventoryAdd />
          </Route>
          <Route path={`${match.path}/smart_inventory/add`}>
            <SmartInventoryAdd />
          </Route>
          <Route path={`${match.path}/inventory/:id`}>
            <Config>
              {({ me }) => (
                <Inventory
                  setBreadcrumb={this.setBreadCrumbConfig}
                  me={me || {}}
                />
              )}
            </Config>
          </Route>
          <Route
            path={`${match.path}/smart_inventory/:id`}
            render={({ match: newRouteMatch }) => (
              <Config>
                {({ me }) => (
                  <SmartInventory
                    history={history}
                    location={location}
                    setBreadcrumb={this.setBreadCrumbConfig}
                    me={me || {}}
                    match={newRouteMatch}
                  />
                )}
              </Config>
            )}
          />
          <Route path={`${match.path}`}>
            <InventoryList />
          </Route>
        </Switch>
      </>
    );
  }
}

export { Inventories as _Inventories };
export default withI18n()(withRouter(Inventories));
