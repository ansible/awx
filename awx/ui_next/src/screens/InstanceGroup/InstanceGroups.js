import React, { useCallback, useEffect, useState } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';

import ScreenHeader from 'components/ScreenHeader';
import InstanceGroupAdd from './InstanceGroupAdd';
import InstanceGroupList from './InstanceGroupList';
import InstanceGroup from './InstanceGroup';
import ContainerGroupAdd from './ContainerGroupAdd';
import ContainerGroup from './ContainerGroup';

function InstanceGroups() {
  const {
    request: settingsRequest,
    isLoading: isSettingsRequestLoading,
    error: settingsRequestError,
    result: isKubernetes,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { IS_K8S },
      } = await SettingsAPI.readCategory('all');
      return IS_K8S;
    }, []),
    { isLoading: true }
  );
  useEffect(() => {
    settingsRequest();
  }, [settingsRequest]);

  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instance_groups': t`Instance Groups`,
    '/instance_groups/add': t`Create new instance group`,
    '/instance_groups/container_group/add': t`Create new container group`,
  });

  const buildBreadcrumbConfig = useCallback((instanceGroups) => {
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
        {!isSettingsRequestLoading && !isKubernetes ? (
          <Route path="/instance_groups/add">
            <InstanceGroupAdd />
          </Route>
        ) : null}
        <Route path="/instance_groups/:id">
          <InstanceGroup setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/instance_groups">
          <InstanceGroupList
            isKubernetes={isKubernetes}
            isSettingsRequestLoading={isSettingsRequestLoading}
            settingsRequestError={settingsRequestError}
          />
        </Route>
      </Switch>
    </>
  );
}

export default InstanceGroups;
