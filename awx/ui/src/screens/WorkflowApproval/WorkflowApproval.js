import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';

import { Card, PageSection } from '@patternfly/react-core';
import { CaretLeftIcon } from '@patternfly/react-icons';
import {
  Link,
  Switch,
  Route,
  Redirect,
  useParams,
  useRouteMatch,
  useLocation,
} from 'react-router-dom';
import useRequest from 'hooks/useRequest';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import { WorkflowApprovalsAPI } from 'api';
import WorkflowApprovalDetail from './WorkflowApprovalDetail';

function WorkflowApproval({ setBreadcrumb }) {
  const { id: workflowApprovalId } = useParams();
  const match = useRouteMatch();
  const location = useLocation();
  const {
    result: { workflowApproval },
    isLoading,
    error,
    request: fetchWorkflowApproval,
  } = useRequest(
    useCallback(async () => {
      const detail = await WorkflowApprovalsAPI.readDetail(workflowApprovalId);
      setBreadcrumb(detail.data);
      return {
        workflowApproval: detail.data,
      };
    }, [workflowApprovalId, setBreadcrumb]),
    { workflowApproval: null }
  );

  useEffect(() => {
    fetchWorkflowApproval();
  }, [fetchWorkflowApproval, location.pathname]);

  if (!isLoading && error) {
    return (
      <PageSection>
        <Card>
          <ContentError error={error}>
            {error.response.status === 404 && (
              <span>
                {t`Workflow Approval not found.`}{' '}
                <Link to="/workflow_approvals">
                  {t`View all Workflow Approvals.`}
                </Link>
              </span>
            )}
          </ContentError>
        </Card>
      </PageSection>
    );
  }

  const tabs = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Workflow Approvals`}
        </>
      ),
      link: `/workflow_approvals`,
      persistentFilterKey: 'workflowApprovals',
      id: 99,
    },
    {
      name: t`Details`,
      link: `${match.url}/details`,
      id: 0,
    },
  ];
  return (
    <PageSection>
      <Card>
        <RoutedTabs tabsArray={tabs} />
        <Switch>
          <Redirect
            from="/workflow_approvals/:id"
            to="/workflow_approvals/:id/details"
            exact
          />
          {workflowApproval && (
            <Route path="/workflow_approvals/:id/details">
              <WorkflowApprovalDetail
                fetchWorkflowApproval={fetchWorkflowApproval}
                workflowApproval={workflowApproval}
              />
            </Route>
          )}
          <Route key="not-found" path="*">
            {!isLoading && (
              <ContentError isNotFound>
                {match.params.id && (
                  <Link to={`/workflow_approvals/${match.params.id}/details`}>
                    {t`View Workflow Approval Details`}
                  </Link>
                )}
              </ContentError>
            )}
          </Route>
        </Switch>
      </Card>
    </PageSection>
  );
}

export default WorkflowApproval;
