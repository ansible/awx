import React, { useEffect, useCallback } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
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
import useRequest from '../../util/useRequest';
import RoutedTabs from '../../components/RoutedTabs';
import ContentError from '../../components/ContentError';
import { WorkflowApprovalsAPI } from '../../api';
import WorkflowApprovalDetail from './WorkflowApprovalDetail';

function WorkflowApproval({ setBreadcrumb, i18n }) {
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
                {i18n._(t`Workflow Approval not found.`)}{' '}
                <Link to="/workflow_approvals">
                  {i18n._(t`View all Workflow Approvals.`)}
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
          {i18n._(t`Back to Workflow Approvals`)}
        </>
      ),
      link: `/workflow_approvals`,
      id: 99,
    },
    {
      name: i18n._(t`Details`),
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
                workflowApproval={workflowApproval}
                isLoading={isLoading}
              />
            </Route>
          )}
          <Route key="not-found" path="*">
            {!isLoading && (
              <ContentError isNotFound>
                {match.params.id && (
                  <Link to={`/workflow_approvals/${match.params.id}/details`}>
                    {i18n._(t`View Workflow Approval Details`)}
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

export default withI18n()(WorkflowApproval);
