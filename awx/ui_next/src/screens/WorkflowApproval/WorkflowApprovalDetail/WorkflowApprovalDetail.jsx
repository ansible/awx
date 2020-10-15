import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link, useHistory, useParams } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import DeleteButton from '../../../components/DeleteButton';
import {
  Detail,
  DetailList,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import WorkflowApprovalStatus from '../shared/WorkflowApprovalStatus';
import { formatDateString, secondsToHHMMSS } from '../../../util/dates';
import { WorkflowApprovalsAPI } from '../../../api';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { WorkflowApproval } from '../../../types';

function WorkflowApprovalDetail({ i18n, workflowApproval }) {
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

  const {
    error: deleteError,
    dismissError: dismissDeleteError,
  } = useDismissableError(deleteApprovalError);

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

  const {
    error: approveError,
    dismissError: dismissApproveError,
  } = useDismissableError(approveApprovalError);

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

  const {
    error: denyError,
    dismissError: dismissDenyError,
  } = useDismissableError(denyApprovalError);

  const sourceWorkflowJob =
    workflowApproval?.summary_fields?.source_workflow_job;

  const sourceWorkflowJobTemplate =
    workflowApproval?.summary_fields?.workflow_job_template;

  const isLoading = isDeleteLoading || isApproveLoading || isDenyLoading;

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={i18n._(t`Name`)}
          value={workflowApproval.name}
          dataCy="wa-detail-name"
        />
        <Detail
          label={i18n._(t`Description`)}
          value={workflowApproval.description}
        />
        {workflowApproval.status === 'pending' && (
          <Detail
            label={i18n._(t`Expires`)}
            value={
              workflowApproval.approval_expiration
                ? formatDateString(workflowApproval.approval_expiration)
                : i18n._(t`Never`)
            }
          />
        )}
        {workflowApproval.status !== 'pending' && (
          <Detail
            label={i18n._(t`Status`)}
            value={
              <WorkflowApprovalStatus workflowApproval={workflowApproval} />
            }
          />
        )}
        {workflowApproval.summary_fields.approved_or_denied_by && (
          <Detail
            label={i18n._(t`Actor`)}
            value={
              <Link
                to={`/users/${workflowApproval.summary_fields.approved_or_denied_by.id}`}
              >
                {workflowApproval.summary_fields.approved_or_denied_by.username}
              </Link>
            }
          />
        )}
        <Detail
          label={i18n._(t`Explanation`)}
          value={workflowApproval.job_explanation}
        />
        <Detail
          label={i18n._(t`Workflow Job`)}
          value={
            sourceWorkflowJob && (
              <Link to={`/jobs/workflow/${sourceWorkflowJob?.id}`}>
                {`${sourceWorkflowJob?.id} - ${sourceWorkflowJob?.name}`}
              </Link>
            )
          }
        />
        <Detail
          label={i18n._(t`Workflow Job Template`)}
          value={
            sourceWorkflowJobTemplate && (
              <Link
                to={`/templates/workflow_job_template/${sourceWorkflowJobTemplate?.id}`}
              >
                {sourceWorkflowJobTemplate?.name}
              </Link>
            )
          }
        />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={workflowApproval.created}
          user={workflowApproval.summary_fields.created_by}
        />
        <Detail
          label={i18n._(t`Last Modified`)}
          value={formatDateString(workflowApproval.modified)}
        />
        <Detail
          label={i18n._(t`Finished`)}
          value={formatDateString(workflowApproval.finished)}
        />
        <Detail
          label={i18n._(t`Canceled`)}
          value={formatDateString(workflowApproval.canceled_on)}
        />
        <Detail
          label={i18n._(t`Elapsed`)}
          value={secondsToHHMMSS(workflowApproval.elapsed)}
        />
      </DetailList>
      <CardActionsRow>
        {workflowApproval.can_approve_or_deny && (
          <>
            <Button
              aria-label={i18n._(t`Approve`)}
              variant="primary"
              onClick={approveWorkflowApproval}
              isDisabled={isLoading}
            >
              {i18n._(t`Approve`)}
            </Button>
            <Button
              aria-label={i18n._(t`Deny`)}
              variant="danger"
              onClick={denyWorkflowApproval}
              isDisabled={isLoading}
            >
              {i18n._(t`Deny`)}
            </Button>
          </>
        )}
        {workflowApproval.summary_fields.user_capabilities &&
          workflowApproval.summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={workflowApproval.name}
              modalTitle={i18n._(t`Delete Workflow Approval`)}
              onConfirm={deleteWorkflowApproval}
              isDisabled={isLoading}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {deleteError && (
        <AlertModal
          isOpen={deleteError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissDeleteError}
        >
          {i18n._(t`Failed to delete workflow approval.`)}
          <ErrorDetail error={deleteError} />
        </AlertModal>
      )}
      {approveError && (
        <AlertModal
          isOpen={approveError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissApproveError}
        >
          {i18n._(t`Failed to approve workflow approval.`)}
          <ErrorDetail error={approveError} />
        </AlertModal>
      )}
      {denyError && (
        <AlertModal
          isOpen={denyError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissDenyError}
        >
          {i18n._(t`Failed to deny workflow approval.`)}
          <ErrorDetail error={denyError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

WorkflowApprovalDetail.defaultProps = {
  workflowApproval: WorkflowApproval.isRequired,
};

export default withI18n()(WorkflowApprovalDetail);
