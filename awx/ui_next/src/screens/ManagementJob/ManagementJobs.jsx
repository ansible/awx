import React, { useState, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Route, Switch } from 'react-router-dom';

import ScreenHeader from '../../components/ScreenHeader';
import ManagementJob from './ManagementJob';
import ManagementJobList from './ManagementJobList';

function ManagementJobs({ i18n }) {
  const basePath = '/management_jobs';

  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    [basePath]: i18n._(t`Management jobs`),
  });

  const buildBreadcrumbConfig = useCallback(
    ({ id, name }, nested) => {
      if (!id) return;

      setBreadcrumbConfig({
        [basePath]: i18n._(t`Management job`),
        [`${basePath}/${id}`]: name,
        [`${basePath}/${id}/notifications`]: i18n._(t`Notifications`),
        [`${basePath}/${id}/schedules`]: i18n._(t`Schedules`),
        [`${basePath}/${id}/schedules/add`]: i18n._(t`Create New Schedule`),
        [`${basePath}/${id}/schedules/${nested?.id}`]: `${nested?.name}`,
        [`${basePath}/${id}/schedules/${nested?.id}/details`]: i18n._(
          t`Details`
        ),
        [`${basePath}/${id}/schedules/${nested?.id}/edit`]: i18n._(
          t`Edit Details`
        ),
      });
    },
    [i18n]
  );

  return (
    <>
      <ScreenHeader streamType="none" breadcrumbConfig={breadcrumbConfig} />
      <Switch>
        <Route path={`${basePath}/:id`}>
          <ManagementJob setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
        <Route path={basePath}>
          <ManagementJobList setBreadcrumb={buildBreadcrumbConfig} />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(ManagementJobs);
