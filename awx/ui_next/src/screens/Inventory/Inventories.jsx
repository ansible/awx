import React, { Component, Fragment } from 'react';
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

  setBreadCrumbConfig = inventory => {
    const { i18n } = this.props;
    if (!inventory) {
      return;
    }
    const inventoryKind =
      inventory.kind === 'smart' ? 'smart_inventory' : 'inventory';
    const breadcrumbConfig = {
      '/inventories': i18n._(t`Inventories`),
      '/inventories/inventory/add': i18n._(t`Create New Inventory`),
      '/inventories/smart_inventory/add': i18n._(t`Create New Smart Inventory`),
      [`/inventories/${inventoryKind}/${inventory.id}`]: `${inventory.name}`,
      [`/inventories/${inventoryKind}/${inventory.id}/details`]: i18n._(
        t`Details`
      ),
      [`/inventories/${inventoryKind}/${inventory.id}/edit`]: i18n._(
        t`Edit Details`
      ),
      [`/inventories/${inventoryKind}/${inventory.id}/access`]: i18n._(
        t`Access`
      ),
      [`/inventories/${inventoryKind}/${inventory.id}/completed_jobs`]: i18n._(
        t`Completed Jobs`
      ),
      [`/inventories/${inventoryKind}/${inventory.id}/hosts`]: i18n._(t`Hosts`),
      [`/inventories/inventory/${inventory.id}/sources`]: i18n._(t`Sources`),
      [`/inventories/inventory/${inventory.id}/groups`]: i18n._(t`Groups`),
    };
    this.setState({ breadcrumbConfig });
  };

  render() {
    const { match, history, location } = this.props;
    const { breadcrumbConfig } = this.state;
    return (
      <Fragment>
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
          <Route
            path={`${match.path}/inventory/:id`}
            render={({ match: newRouteMatch }) => (
              <Config>
                {({ me }) => (
                  <Inventory
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
      </Fragment>
    );
  }
}

export { Inventories as _Inventories };
export default withI18n()(withRouter(Inventories));
