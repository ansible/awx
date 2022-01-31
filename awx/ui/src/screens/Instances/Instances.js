import React, { useCallback, useState } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';
import ScreenHeader from 'components/ScreenHeader';
import { InstanceList } from './InstanceList';
import Instance from './Instance';

function Instances() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instances': t`Instances`,
  });

  const buildBreadcrumbConfig = useCallback((instance) => {
    if (!instance) {
      return;
    }
    setBreadcrumbConfig({
      '/instances': t`Instances`,
      [`/instances/${instance.id}`]: t`${instance.hostname}`,
      [`/instances/${instance.id}/details`]: t`Details`,
    });
  }, []);

  return (
    <>
      <ScreenHeader
        streamType="instances"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/instances/:id">
          <Instance setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instances">
          <InstanceList />
        </Route>
      </Switch>
    </>
  );
}

export default Instances;
