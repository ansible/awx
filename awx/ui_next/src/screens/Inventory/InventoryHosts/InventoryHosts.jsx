import React from 'react';
import { Switch, Route, withRouter } from 'react-router-dom';

import Host from '../../Host/Host';
import InventoryHostList from './InventoryHostList';
import HostAdd from '../InventoryHostAdd';

function InventoryHosts({ match, setBreadcrumb, i18n, inventory }) {
  return (
    <Switch>
      <Route
        key="host-add"
        path="/inventories/inventory/:id/hosts/add"
        render={() => <HostAdd match={match} />}
      />
      ,
      <Route
        key="details and edit"
        path="/inventories/inventory/:id/hosts/:hostId"
        render={() => (
          <Host
            setBreadcrumb={setBreadcrumb}
            match={match}
            i18n={i18n}
            inventory={inventory}
          />
        )}
      />
      ,
      <Route
        key="host-list"
        path="/inventories/inventory/:id/hosts/"
        render={() => (
          <InventoryHostList
            match={match}
            setBreadcrumb={setBreadcrumb}
            i18n={i18n}
          />
        )}
      />
      ,
    </Switch>
  );
}

export default withRouter(InventoryHosts);
