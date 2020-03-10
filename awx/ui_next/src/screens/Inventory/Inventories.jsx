import React, { Component } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, withRouter, Switch } from 'react-router-dom';

import { Config } from '@contexts/Config';
import Breadcrumbs from '@components/Breadcrumbs/Breadcrumbs';
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
        '/inventories/inventory/add': i18n._(t`Create New Inventory`),
        '/inventories/smart_inventory/add': i18n._(
          t`Create New Smart Inventory`
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
    const inventoryHostsPath = `/inventories/${inventoryKind}/${inventory.id}/hosts`;
    const inventoryGroupsPath = `/inventories/${inventoryKind}/${inventory.id}/groups`;

    const breadcrumbConfig = {
      '/inventories': i18n._(t`Inventories`),
      '/inventories/inventory/add': i18n._(t`Create New Inventory`),
      '/inventories/smart_inventory/add': i18n._(t`Create New Smart Inventory`),

      [inventoryPath]: `${inventory.name}`,
      [`${inventoryPath}/access`]: i18n._(t`Access`),
      [`${inventoryPath}/completed_jobs`]: i18n._(t`Completed Jobs`),
      [`${inventoryPath}/details`]: i18n._(t`Details`),
      [`${inventoryPath}/edit`]: i18n._(t`Edit Details`),
      [`${inventoryPath}/sources`]: i18n._(t`Sources`),

      [inventoryHostsPath]: i18n._(t`Hosts`),
      [`${inventoryHostsPath}/add`]: i18n._(t`Create New Host`),
      [`${inventoryHostsPath}/${nested?.id}`]: `${nested?.name}`,
      [`${inventoryHostsPath}/${nested?.id}/edit`]: i18n._(t`Edit Details`),
      [`${inventoryHostsPath}/${nested?.id}/details`]: i18n._(t`Host Details`),
      [`${inventoryHostsPath}/${nested?.id}/completed_jobs`]: i18n._(
        t`Completed Jobs`
      ),

      [inventoryGroupsPath]: i18n._(t`Groups`),
      [`${inventoryGroupsPath}/add`]: i18n._(t`Create New Group`),
      [`${inventoryGroupsPath}/${nested?.id}`]: `${nested?.name}`,
      [`${inventoryGroupsPath}/${nested?.id}/edit`]: i18n._(t`Edit Details`),
      [`${inventoryGroupsPath}/${nested?.id}/details`]: i18n._(
        t`Group Details`
      ),
      [`${inventoryGroupsPath}/${nested?.id}/nested_hosts`]: i18n._(t`Hosts`),
      [`${inventoryGroupsPath}/${nested?.id}/nested_hosts/add`]: i18n._(
        t`Create New Host`
      ),
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
          <Route
            path={`${match.path}/inventory/add`}
            render={() => <InventoryAdd />}
          />
          <Route
            path={`${match.path}/smart_inventory/add`}
            render={() => <SmartInventoryAdd />}
          />
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
          <Route path={`${match.path}`} render={() => <InventoryList />} />
        </Switch>
      </>
    );
  }
}

export { Inventories as _Inventories };
export default withI18n()(withRouter(Inventories));
