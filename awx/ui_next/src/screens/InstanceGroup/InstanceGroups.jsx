import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import InstanceGroupAdd from './InstanceGroupAdd';
import InstanceGroupList from './InstanceGroupList';
import InstanceGroup from './InstanceGroup';
import Breadcrumbs from '../../components/Breadcrumbs';

function InstanceGroups({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/instance_groups': i18n._(t`Instance Groups`),
    '/instance_groups/add': i18n._(t`Create Instance Groups`),
  });

  const buildBreadcrumbConfig = useCallback(
    instanceGroups => {
      if (!instanceGroups) {
        return;
      }
      setBreadcrumbConfig({
        '/instance_groups': i18n._(t`Instance Groups`),
        '/instance_groups/add': i18n._(t`Create Instance Groups`),
        [`/instance_groups/${instanceGroups.id}`]: `${instanceGroups.name}`,
      });
    },
    [i18n]
  );
  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
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

export default withI18n()(InstanceGroups);
