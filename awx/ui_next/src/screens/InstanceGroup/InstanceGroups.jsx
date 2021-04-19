import React, { useState, useCallback } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import InstanceGroupAdd from './InstanceGroupAdd';
import InstanceGroupList from './InstanceGroupList';
import InstanceGroup from './InstanceGroup';

import ContainerGroupAdd from './ContainerGroupAdd';
import ContainerGroup from './ContainerGroup';
import ScreenHeader from '../../components/ScreenHeader';

function InstanceGroups() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instance_groups': t`Instance Groups`,
    '/instance_groups/add': t`Create new instance group`,
    '/instance_groups/container_group/add': t`Create new container group`,
  });

  const buildBreadcrumbConfig = useCallback(instanceGroups => {
    if (!instanceGroups) {
      return;
    }
    setBreadcrumbConfig({
      '/instance_groups': t`Instance Groups`,
      '/instance_groups/add': t`Create new instance group`,
      '/instance_groups/container_group/add': t`Create new container group`,

      [`/instance_groups/${instanceGroups.id}/details`]: t`Details`,
      [`/instance_groups/${instanceGroups.id}/instances`]: t`Instances`,
      [`/instance_groups/${instanceGroups.id}/jobs`]: t`Jobs`,
      [`/instance_groups/${instanceGroups.id}/edit`]: t`Edit details`,
      [`/instance_groups/${instanceGroups.id}`]: `${instanceGroups.name}`,

      [`/instance_groups/container_group/${instanceGroups.id}/details`]: t`Details`,
      [`/instance_groups/container_group/${instanceGroups.id}/jobs`]: t`Jobs`,
      [`/instance_groups/container_group/${instanceGroups.id}/edit`]: t`Edit details`,
      [`/instance_groups/container_group/${instanceGroups.id}`]: `${instanceGroups.name}`,
    });
  }, []);
  return (
    <>
      <ScreenHeader
        streamType="instance_group"
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
          <InstanceGroupList />
        </Route>
      </Switch>
    </>
  );
}

export default InstanceGroups;
