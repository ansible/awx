import React, { useState, useCallback } from 'react';

import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';
import PersistentFilters from 'components/PersistentFilters';
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import ExecutionEnvironment from './ExecutionEnvironment';
import ExecutionEnvironmentAdd from './ExecutionEnvironmentAdd';
import ExecutionEnvironmentList from './ExecutionEnvironmentList';

function ExecutionEnvironments() {
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/execution_environments': t`Execution Environments`,
    '/execution_environments/add': t`Create new execution environment`,
  });

  const buildBreadcrumbConfig = useCallback((executionEnvironments) => {
    if (!executionEnvironments) {
      return;
    }
    setBreadcrumbConfig({
      '/execution_environments': t`Execution Environments`,
      '/execution_environments/add': t`Create new execution environment`,
      [`/execution_environments/${executionEnvironments.id}`]: `${executionEnvironments.name}`,
      [`/execution_environments/${executionEnvironments.id}/edit`]: t`Edit details`,
      [`/execution_environments/${executionEnvironments.id}/details`]: t`Details`,
    });
  }, []);
  return (
    <>
      <ScreenHeader
        streamType="execution_environment"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path="/execution_environments/add">
          <ExecutionEnvironmentAdd />
        </Route>
        <Route path="/execution_environments/:id">
          <ExecutionEnvironment setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path="/execution_environments">
          <PersistentFilters pageKey="executionEnvironments">
            <ExecutionEnvironmentList />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}
export default ExecutionEnvironments;
