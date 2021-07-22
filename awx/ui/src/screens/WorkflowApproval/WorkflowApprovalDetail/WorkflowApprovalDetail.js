import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory, useParams } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import DeleteButton from 'components/DeleteButton';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import ErrorDetail from 'components/ErrorDetail';
import { formatDateString, secondsToHHMMSS } from 'util/dates';
import { WorkflowApprovalsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { WorkflowApproval } from 'types';
import WorkflowApprovalStatus from '../shared/WorkflowApprovalStatus';

function WorkflowApprovalDetail({ workflowApproval }) {
  const { id: workflowApprovalId } = useParams();
  const history = useHistory();
  const {
    request: deleteWorkflowApproval,
    isLoading: isDeleteLoading,
    error: deleteApprovalError,
  } = useRequest(
    useCallback(async () => {
      await WorkflowApprovalsAPI.destroy(workflowApprovalId);
      history.push(`/workflow_approvals`);
    }, [workflowApprovalId, history])
  );

  const { error: deleteError, dismissError: dismissDeleteError } =
    useDismissableError(deleteApprovalError);

  const {
    error: approveApprovalError,
    isLoading: isApproveLoading,
    request: approveWorkflowApproval,
  } = useRequest(
    useCallback(async () => {
      await WorkflowApprovalsAPI.approve(workflowApprovalId);
      history.push(`/workflow_approvals/${workflowApprovalId}`);
    }, [workflowApprovalId, history]),
    {}
  );

  const { error: approveError, dismissError: dismissApproveError } =
    useDismissableError(approveApprovalError);

  const {
    error: denyApprovalError,
    isLoading: isDenyLoading,
    request: denyWorkflowApproval,
  } = useRequest(
    useCallback(async () => {
      await WorkflowApprovalsAPI.deny(workflowApprovalId);
      history.push(`/workflow_approvals/${workflowApprovalId}`);
    }, [workflowApprovalId, history]),
    {}
  );

  const { error: denyError, dismissError: dismissDenyError } =
    useDismissableError(denyApprovalError);

  const sourceWorkflowJob =
    workflowApproval?.summary_fields?.source_workflow_job;

  const sourceWorkflowJobTemplate =
    workflowApproval?.summary_fields?.workflow_job_template;

  const isLoading = isDeleteLoading || isApproveLoading || isDenyLoading;

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={t`Name`}
          value={workflowApproval.name}
          dataCy="wa-detail-name"
        />
        <Detail
          label={t`Description`}
          value={workflowApproval.description}
          dataCy="wa-detail-description"
        />
        {workflowApproval.status === 'pending' && (
          <Detail
            label={t`Expires`}
            value={
              workflowApproval.approval_expiration
                ? formatDateString(workflowApproval.approval_expiration)
                : t`Never`
            }
            dataCy="wa-detail-expires"
          />
        )}
        {workflowApproval.status !== 'pending' && (
          <Detail
            label={t`Status`}
            value={
              <WorkflowApprovalStatus workflowApproval={workflowApproval} />
            }
            dataCy="wa-detail-status"
          />
        )}
        {workflowApproval.summary_fields.approved_or_denied_by && (
          <Detail
            label={t`Actor`}
            value={
              <Link
                to={`/users/${workflowApproval.summary_fields.approved_or_denied_by.id}`}
              >
                {workflowApproval.summary_fields.approved_or_denied_by.username}
              </Link>
            }
            dataCy="wa-detail-actor"
          />
        )}
        <Detail
          label={t`Explanation`}
          value={workflowApproval.job_explanation}
          dataCy="wa-detail-explanation"
        />
        <Detail
          label={t`Workflow Job`}
          value={
            sourceWorkflowJob && sourceWorkflowJob?.id ? (
              <Link to={`/jobs/workflow/${sourceWorkflowJob?.id}`}>
                {`${sourceWorkflowJob?.id} - ${sourceWorkflowJob?.name}`}
              </Link>
            ) : (
              t`Deleted`
            )
          }
          dataCy="wa-detail-source-job"
        />
        <Detail
          label={t`Workflow Job Template`}
          value={
            sourceWorkflowJobTemplate && (
              <Link
                to={`/templates/workflow_job_template/${sourceWorkflowJobTemplate?.id}`}
              >
                {sourceWorkflowJobTemplate?.name}
              </Link>
            )
          }
          dataCy="wa-detail-source-workflow"
        />
        <UserDateDetail
          label={t`Created`}
          date={workflowApproval.created}
          user={workflowApproval.summary_fields.created_by}
          dataCy="wa-detail-created-by"
        />
        <Detail
          label={t`Last Modified`}
          value={formatDateString(workflowApproval.modified)}
          dataCy="wa-detail-last-modified"
        />
        <Detail
          label={t`Finished`}
          value={formatDateString(workflowApproval.finished)}
          dataCy="wa-detail-finished"
        />
        <Detail
          label={t`Canceled`}
          value={formatDateString(workflowApproval.canceled_on)}
          dataCy="wa-detail-canceled"
        />
        <Detail
          label={t`Elapsed`}
          value={secondsToHHMMSS(workflowApproval.elapsed)}
          dataCy="wa-detail-elapsed"
        />
      </DetailList>
      <CardActionsRow>
        {workflowApproval.can_approve_or_deny && (
          <>
            <Button
              ouiaId={`${workflowApproval.id}-approve-button`}
              aria-label={t`Approve`}
              variant="primary"
              onClick={approveWorkflowApproval}
              isDisabled={isLoading}
            >
              {t`Approve`}
            </Button>
            <Button
              ouiaId={`${workflowApproval.id}-deny-button`}
              aria-label={t`Deny`}
              variant="danger"
              onClick={denyWorkflowApproval}
              isDisabled={isLoading}
            >
              {t`Deny`}
            </Button>
          </>
        )}
        {workflowApproval.status !== 'pending' &&
          workflowApproval.summary_fields.user_capabilities &&
          workflowApproval.summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={workflowApproval.name}
              modalTitle={t`Delete Workflow Approval`}
              onConfirm={deleteWorkflowApproval}
              isDisabled={isLoading}
            >
              {t`Delete`}
            </DeleteButton>
          )}
      </CardActionsRow>
      {deleteError && (
        <AlertModal
          isOpen={deleteError}
          variant="error"
          title={t`Error!`}
          onClose={dismissDeleteError}
        >
          {t`Failed to delete workflow approval.`}
          <ErrorDetail error={deleteError} />
        </AlertModal>
      )}
      {approveError && (
        <AlertModal
          isOpen={approveError}
          variant="error"
          title={t`Error!`}
          onClose={dismissApproveError}
        >
          {t`Failed to approve workflow approval.`}
          <ErrorDetail error={approveError} />
        </AlertModal>
      )}
      {denyError && (
        <AlertModal
          isOpen={denyError}
          variant="error"
          title={t`Error!`}
          onClose={dismissDenyError}
        >
          {t`Failed to deny workflow approval.`}
          <ErrorDetail error={denyError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

WorkflowApprovalDetail.defaultProps = {
  workflowApproval: WorkflowApproval.isRequired,
};

export default WorkflowApprovalDetail;
