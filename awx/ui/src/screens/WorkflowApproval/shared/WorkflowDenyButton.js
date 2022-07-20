import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { OutlinedThumbsDownIcon } from '@patternfly/react-icons';
import { WorkflowApprovalsAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';

import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { getStatus } from './WorkflowApprovalUtils';

function WorkflowDenyButton({ isDetailView, workflowApproval }) {
  const hasBeenActedOn = workflowApproval.status === 'failed';
  const { id } = workflowApproval;

  const { error: denyApprovalError, request: denyWorkflowApprovals } =
    useRequest(
      useCallback(async () => WorkflowApprovalsAPI.deny(id), [id]),
      {}
    );

  const handleDeny = async () => {
    await denyWorkflowApprovals();
  };

  const { error: denyError, dismissError: dismissDenyError } =
    useDismissableError(denyApprovalError);

  return (
    <>
      <Button
        aria-label={
          hasBeenActedOn
            ? t`This workflow has already been ${getStatus(workflowApproval)}`
            : t`Deny`
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
