import React, { useCallback, useState } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';
import ScreenHeader from 'components/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import { InstanceList } from './InstanceList';
import Instance from './Instance';
import InstanceAdd from './InstanceAdd';
import InstanceEdit from './InstanceEdit';

function Instances() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instances': t`Instances`,
    '/instances/add': t`Create new Instance`,
  });

  const buildBreadcrumbConfig = useCallback((instance) => {
    if (!instance) {
      return;
    }
    setBreadcrumbConfig({
      '/instances': t`Instances`,
      '/instances/add': t`Create new Instance`,
      [`/instances/${instance.id}`]: `${instance.hostname}`,
      [`/instances/${instance.id}/details`]: t`Details`,
      [`/instances/${instance.id}/peers`]: t`Peers`,
      [`/instances/${instance.id}/endpoints`]: t`Endpoints`,
      [`/instances/${instance.id}/edit`]: t`Edit Instance`,
    });
  }, []);

  return (
    <>
      <ScreenHeader streamType="instance" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/instances/add">
          <InstanceAdd setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instances/:id/edit" key="edit">
          <InstanceEdit setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instances/:id">
          <Instance setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instances">
          <PersistentFilters pageKey="instances">
            <InstanceList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export default Instances;
