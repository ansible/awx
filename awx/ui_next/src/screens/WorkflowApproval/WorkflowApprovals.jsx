import React, { useState, useCallback } from 'react';
import { Route, Switch, useRouteMatch } from 'react-router-dom';

import { t } from '@lingui/macro';
import WorkflowApprovalList from './WorkflowApprovalList';
import WorkflowApproval from './WorkflowApproval';
import ScreenHeader from '../../components/ScreenHeader/ScreenHeader';

function WorkflowApprovals() {
  const match = useRouteMatch();
  const [breadcrumbConfig, setBreadcrumbConfig] = useState({
    '/workflow_approvals': t`Workflow Approvals`,
  });

  const updateBreadcrumbConfig = useCallback(workflowApproval => {
    const { id } = workflowApproval;
    setBreadcrumbConfig({
      '/workflow_approvals': t`Workflow Approvals`,
      [`/workflow_approvals/${id}`]: workflowApproval.name,
      [`/workflow_approvals/${id}/details`]: t`Details`,
    });
  }, []);

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

export default WorkflowApprovals;
