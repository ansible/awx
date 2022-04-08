import React, { useCallback, useState } from 'react';

import { t } from '@lingui/macro';
import { Link, useHistory, useParams } from 'react-router-dom';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import DeleteButton from 'components/DeleteButton';
import { Detail, DetailList, UserDateDetail } from 'components/DetailList';
import ErrorDetail from 'components/ErrorDetail';
import { formatDateString, secondsToHHMMSS } from 'util/dates';
import { WorkflowApprovalsAPI, WorkflowJobsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { WorkflowApproval } from 'types';
import StatusLabel from 'components/StatusLabel';
import {
  getDetailPendingLabel,
  getStatus,
} from '../shared/WorkflowApprovalUtils';
import WorkflowApprovalControls from '../shared/WorkflowApprovalControls';

function WorkflowApprovalDetail({ workflowApproval }) {
  const { id: workflowApprovalId } = useParams();
  const [isKebabOpen, setIsKebabModalOpen] = useState(false);
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

  const {
    error: cancelApprovalError,
    isLoading: isCancelLoading,
    request: cancelWorkflowApprovals,
  } = useRequest(
    useCallback(async () => {
      await WorkflowJobsAPI.cancel(
        workflowApproval.summary_fields.source_workflow_job.id
      );
      history.push(`/workflow_approvals/${workflowApprovalId}`);
    }, [workflowApproval, workflowApprovalId, history]),
    {}
  );

  const handleCancel = async () => {
    setIsKebabModalOpen(false);
    await cancelWorkflowApprovals();
  };

  const { error: cancelError, dismissError: dismissCancelError } =
    useDismissableError(cancelApprovalError);

  const sourceWorkflowJob =
    workflowApproval?.summary_fields?.source_workflow_job;

  const sourceWorkflowJobTemplate =
    workflowApproval?.summary_fields?.workflow_job_template;

  const isLoading =
    isDeleteLoading || isApproveLoading || isDenyLoading || isCancelLoading;

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
              <StatusLabel status={workflowApproval.status}>
                {getDetailPendingLabel(workflowApproval)}
              </StatusLabel>
            }
            dataCy="wa-detail-expires"
          />
        )}
        {workflowApproval.status !== 'pending' && (
          <Detail
            label={t`Status`}
            value={<StatusLabel status={getStatus(workflowApproval)} />}
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
        />
        <Detail
          label={t`Last Modified`}
          value={formatDateString(workflowApproval.modified)}
        />
        <Detail
          label={t`Finished`}
          value={formatDateString(workflowApproval.finished)}
        />
        <Detail
          label={t`Canceled`}
          value={formatDateString(workflowApproval.canceled_on)}
        />
        <Detail
          label={t`Elapsed`}
          value={secondsToHHMMSS(workflowApproval.elapsed)}
        />
      </DetailList>
      <CardActionsRow>
        {workflowApproval.status === 'pending' &&
          workflowApproval.can_approve_or_deny && (
            <WorkflowApprovalControls
              selected={[workflowApproval]}
              onHandleApprove={approveWorkflowApproval}
              onHandleDeny={denyWorkflowApproval}
              onHandleCancel={handleCancel}
              onHandleToggleToolbarKebab={(isOpen) =>
                setIsKebabModalOpen(isOpen)
              }
              isKebabOpen={isKebabOpen}
            />
          )}
        {workflowApproval.status !== 'pending' &&
          workflowApproval.summary_fields?.user_capabilities?.delete && (
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
      {cancelError && (
        <AlertModal
          isOpen={cancelError}
          variant="error"
          title={t`Error!`}
          onClose={dismissCancelError}
        >
          {t`Failed to approve workflow approval.`}
          <ErrorDetail error={cancelError} />
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
