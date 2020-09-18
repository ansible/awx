import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import ExecutionEnvironment from './ExecutionEnvironment';
import ExecutionEnvironmentAdd from './ExecutionEnvironmentAdd';
import ExecutionEnvironmentList from './ExecutionEnvironmentList';
import Breadcrumbs from '../../components/Breadcrumbs';

function ExecutionEnvironments({ i18n }) {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/execution_environments': i18n._(t`Execution environments`),
    '/execution_environments/add': i18n._(t`Create Execution environments`),
  });

  const buildBreadcrumbConfig = useCallback(
    executionEnvironments => {
      if (!executionEnvironments) {
        return;
      }
      setBreadcrumbConfig({
        '/execution_environments': i18n._(t`Execution environments`),
        '/execution_environments/add': i18n._(t`Create Execution environments`),
        [`/execution_environments/${executionEnvironments.id}`]: `${executionEnvironments.image}`,
        [`/execution_environments/${executionEnvironments.id}/edit`]: i18n._(
          t`Edit details`
        ),
        [`/execution_environments/${executionEnvironments.id}/details`]: i18n._(
          t`Details`
        ),
      });
    },
    [i18n]
  );
  return (
    <>
      <Breadcrumbs breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path="/execution_environments/add">
          <ExecutionEnvironmentAdd />
        </Route>
        <Route path="/execution_environments/:id">
          <ExecutionEnvironment setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/execution_environments">
          <ExecutionEnvironmentList />
        </Route>
      </Switch>
    </>
  );
}
export default withI18n()(ExecutionEnvironments);
