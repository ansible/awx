import React, { useState, useCallback } from 'react';
import { Route, Switch } from 'react-router-dom';
import { t } from '@lingui/macro';

import { Config } from 'contexts/Config';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import HostList from './HostList';
import HostAdd from './HostAdd';
import Host from './Host';

function Hosts() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/hosts': t`Hosts`,
    '/hosts/add': t`Create New Host`,
  });

  const buildBreadcrumbConfig = useCallback((host) => {
    if (!host) {
      return;
    }
    setBreadcrumbConfig({
      '/hosts': t`Hosts`,
      '/hosts/add': t`Create New Host`,
      [`/hosts/${host.id}`]: `${host.name}`,
      [`/hosts/${host.id}/edit`]: t`Edit Details`,
      [`/hosts/${host.id}/details`]: t`Details`,
      [`/hosts/${host.id}/facts`]: t`Facts`,
      [`/hosts/${host.id}/groups`]: t`Groups`,
      [`/hosts/${host.id}/jobs`]: t`Jobs`,
    });
  }, []);

  return (
    <>
      <ScreenHeader streamType="host" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/hosts/add">
          <HostAdd />
        </Route>
        <Route path="/hosts/:id">
          <Config>
            {({ me }) => (
              <Host setBreadcrumb={buildBreadcrumbConfig} me={me || {}} />
            )}
          </Config>
        </Route>
        <Route path="/hosts">
          <PersistentFilters pageKey="hosts">
            <HostList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export { Hosts as _Hosts };
export default Hosts;
