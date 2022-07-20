import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { OutlinedThumbsUpIcon } from '@patternfly/react-icons';
import { WorkflowApprovalsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';

import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { getStatus } from './WorkflowApprovalUtils';

function WorkflowApprovalButton({ isDetailView, workflowApproval }) {
  const { id } = workflowApproval;
  const hasBeenActedOn = workflowApproval.status === 'successful';
  const { error: approveApprovalError, request: approveWorkflowApprovals } =
    useRequest(
      useCallback(async () => WorkflowApprovalsAPI.approve(id), [id]),
      {}
    );

  const handleApprove = async () => {
    await approveWorkflowApprovals();
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
