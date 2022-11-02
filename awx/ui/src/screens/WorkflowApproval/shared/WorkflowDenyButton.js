import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { OutlinedThumbsDownIcon } from '@patternfly/react-icons';
import { WorkflowApprovalsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';

import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';

function WorkflowDenyButton({ isDetailView, workflowApproval, onHandleToast }) {
  const hasBeenActedOn =
    Object.keys(workflowApproval.summary_fields.approved_or_denied_by || {})
      .length > 0 || workflowApproval.status === 'canceled';

  const { id } = workflowApproval;
  const { error: denyApprovalError, request: denyWorkflowApprovals } =
    useRequest(
      useCallback(async () => WorkflowApprovalsAPI.deny(id), [id]),
      {}
    );

  const handleDeny = async () => {
    await denyWorkflowApprovals();
    onHandleToast(workflowApproval.id, t`Successfully Denied`);
  };

  const { error: denyError, dismissError: dismissDenyError } =
    useDismissableError(denyApprovalError);

  return (
    <>
      <Button
        aria-label={
          hasBeenActedOn ? t`This workflow has already been acted on` : t`Deny`
        }
        ouiaId="workflow-deny-button"
        isDisabled={hasBeenActedOn}
        variant={isDetailView ? 'secondary' : 'plain'}
        onClick={() => handleDeny()}
      >
        {isDetailView ? t`Deny` : <OutlinedThumbsDownIcon />}
      </Button>
      {denyError && (
        <AlertModal
          isOpen={denyError}
          variant="error"
          title={t`Error!`}
          onClose={dismissDenyError}
        >
          {t`Failed to deny ${workflowApproval.name}.`}
          <ErrorDetail error={denyError} />
        </AlertModal>
      )}
    </>
  );
}
export default WorkflowDenyButton;
