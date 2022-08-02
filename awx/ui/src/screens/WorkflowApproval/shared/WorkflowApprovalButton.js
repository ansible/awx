import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { OutlinedThumbsUpIcon } from '@patternfly/react-icons';
import { WorkflowApprovalsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';

import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { getStatus } from './WorkflowApprovalUtils';

function WorkflowApprovalButton({
  isDetailView,
  workflowApproval,
  onHandleToast,
}) {
  const { id } = workflowApproval;
  const hasBeenActedOn =
    Object.keys(workflowApproval.summary_fields.approved_or_denied_by || {})
      .length > 0 || workflowApproval.status === 'canceled';
  const { error: approveApprovalError, request: approveWorkflowApprovals } =
    useRequest(
      useCallback(async () => WorkflowApprovalsAPI.approve(id), [id]),
      {}
    );

  const handleApprove = async () => {
    await approveWorkflowApprovals();
    onHandleToast(workflowApproval.id, t`Successfully Approved`);
  };

  const { error: approveError, dismissError: dismissApproveError } =
    useDismissableError(approveApprovalError);

  return (
    <>
      <Button
        isDisabled={hasBeenActedOn}
        variant={isDetailView ? 'primary' : 'plain'}
        ouiaId="workflow-approve-button"
        onClick={() => handleApprove()}
        aria-label={
          hasBeenActedOn
            ? t`This workflow has already been ${getStatus(workflowApproval)}`
            : t`Approve`
        }
      >
        {isDetailView ? t`Approve` : <OutlinedThumbsUpIcon />}
      </Button>
      {approveError && (
        <AlertModal
          isOpen={approveError}
          variant="error"
          title={t`Error!`}
          onClose={dismissApproveError}
        >
          {t`Failed to approve ${workflowApproval.name}.`}
          <ErrorDetail error={approveError} />
        </AlertModal>
      )}
    </>
  );
}
export default WorkflowApprovalButton;
