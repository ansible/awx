import React, { useState, useCallback } from 'react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';
import ScreenHeader from 'components/ScreenHeader';
import PersistentFilters from 'components/PersistentFilters';
import ManagementJob from './ManagementJob';
import ManagementJobList from './ManagementJobList';

function ManagementJobs() {
  const basePath = '/management_jobs';

  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    [basePath]: t`Management jobs`,
  });

  const buildBreadcrumbConfig = useCallback(({ id, name }, nested) => {
    if (!id) return;

    setBreadcrumbConfig({
      [basePath]: t`Management job`,
      [`${basePath}/${id}`]: name,
      [`${basePath}/${id}/notifications`]: t`Notifications`,
      [`${basePath}/${id}/schedules`]: t`Schedules`,
      [`${basePath}/${id}/schedules/add`]: t`Create New Schedule`,
      [`${basePath}/${id}/schedules/${nested?.id}`]: `${nested?.name}`,
      [`${basePath}/${id}/schedules/${nested?.id}/details`]: t`Details`,
      [`${basePath}/${id}/schedules/${nested?.id}/edit`]: t`Edit Details`,
    });
  }, []);

  return (
    <>
      <ScreenHeader streamType="none" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path={`${basePath}/:id`}>
          <ManagementJob setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path={basePath}>
          <PersistentFilters pageKey="managementJobs">
            <ManagementJobList setBreadcrumb={buildBreadcrumbConfig} />
          </PersistentFilters>
        </Route>
      </Switch>
    </>
  );
}

export default ManagementJobs;
