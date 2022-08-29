import React, { useCallback, useState } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch, useLocation } from 'react-router-dom';
import ScreenHeader from 'components/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import InstanceGroupAdd from './InstanceGroupAdd';
import InstanceGroupList from './InstanceGroupList';
import InstanceGroup from './InstanceGroup';
import ContainerGroupAdd from './ContainerGroupAdd';
import ContainerGroup from './ContainerGroup';

function InstanceGroups() {
  const { pathname } = useLocation();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instance_groups': t`Instance Groups`,
    '/instance_groups/add': t`Create new instance group`,
    '/instance_groups/container_group/add': t`Create new container group`,
  });

  const buildBreadcrumbConfig = useCallback((instanceGroups, instance) => {
    if (!instanceGroups) {
      return;
    }
    setBreadcrumbConfig({
      '/instance_groups': t`Instance Groups`,
      '/instance_groups/add': t`Create new instance group`,
      '/instance_groups/container_group/add': t`Create new container group`,

      [`/instance_groups/${instanceGroups.id}/details`]: t`Details`,
      [`/instance_groups/${instanceGroups.id}/instances`]: t`Instances`,
      [`/instance_groups/${instanceGroups.id}/instances/${instance?.id}`]: `${instance?.hostname}`,
      [`/instance_groups/${instanceGroups.id}/instances/${instance?.id}/details`]: t`Instance details`,
      [`/instance_groups/${instanceGroups.id}/jobs`]: t`Jobs`,
      [`/instance_groups/${instanceGroups.id}/edit`]: t`Edit details`,
      [`/instance_groups/${instanceGroups.id}`]: `${instanceGroups.name}`,

      [`/instance_groups/container_group/${instanceGroups.id}/details`]: t`Details`,
      [`/instance_groups/container_group/${instanceGroups.id}/jobs`]: t`Jobs`,
      [`/instance_groups/container_group/${instanceGroups.id}/edit`]: t`Edit details`,
      [`/instance_groups/container_group/${instanceGroups.id}`]: `${instanceGroups.name}`,
    });
  }, []);

  const streamType = pathname.includes('instances')
    ? 'instance'
    : 'instance_group';

  return (
    <>
      <ScreenHeader
        streamType={streamType}
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/instance_groups/container_group/add">
          <ContainerGroupAdd />
        </Route>
        <Route path="/instance_groups/container_group/:id">
          <ContainerGroup setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instance_groups/add">
          <InstanceGroupAdd />
        </Route>
        <Route path="/instance_groups/:id">
          <InstanceGroup setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instance_groups">
          <PersistentFilters pageKey="instanceGroups">
            <InstanceGroupList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export default InstanceGroups;
