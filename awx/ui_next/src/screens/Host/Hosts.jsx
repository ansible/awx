import React, { useState, useCallback } from 'react';
import { Route, Switch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Config } from '../../contexts/Config';
import Breadcrumbs from '../../components/Breadcrumbs/Breadcrumbs';

import HostList from './HostList';
import HostAdd from './HostAdd';
import Host from './Host';

function Hosts({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/hosts': i18n._(t`Hosts`),
    '/hosts/add': i18n._(t`Create New Host`),
  });

  const buildBreadcrumbConfig = useCallback(
    host => {
      if (!host) {
        return;
      }
      setBreadcrumbConfig({
        '/hosts': i18n._(t`Hosts`),
        '/hosts/add': i18n._(t`Create New Host`),
        [`/hosts/${host.id}`]: `${host.name}`,
        [`/hosts/${host.id}/edit`]: i18n._(t`Edit Details`),
        [`/hosts/${host.id}/details`]: i18n._(t`Details`),
        [`/hosts/${host.id}/facts`]: i18n._(t`Facts`),
        [`/hosts/${host.id}/groups`]: i18n._(t`Groups`),
        [`/hosts/${host.id}/completed_jobs`]: i18n._(t`Completed Jobs`),
      });
    },
    [i18n]
  );

  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
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
          <HostList />
        </Route>
      </Switch>
    </>
  );
}

export { Hosts as _Hosts };
export default withI18n()(Hosts);
