import React, { useState, useCallback } from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import WorkflowApprovalList from './WorkflowApprovalList';
import WorkflowApproval from './WorkflowApproval';
import ScreenHeader from '../../components/ScreenHeader/ScreenHeader';

function WorkflowApprovals({ i18n }) {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/workflow_approvals': i18n._(t`Workflow Approvals`),
  });

  const updateBreadcrumbConfig = useCallback(
    workflowApproval => {
      const { id } = workflowApproval;
      setBreadcrumbConfig({
        '/workflow_approvals': i18n._(t`Workflow Approvals`),
        [`/workflow_approvals/${id}`]: workflowApproval.name,
        [`/workflow_approvals/${id}/details`]: i18n._(t`Details`),
      });
    },
    [i18n]
  );

  return (
    <>
      <ScreenHeader
        streamType="workflow_approval"
        breadcrumbConfig={breadcrumbConfig}
      />
      <Switch>
        <Route path={`${match.url}/:id`}>
          <WorkflowApproval setBreadcrumb={updateBreadcrumbConfig} />
        </Route>
        <Route path={`${match.url}`}>
          <WorkflowApprovalList />
        </Route>
      </Switch>
    </>
  );
}

export default withI18n()(WorkflowApprovals);
