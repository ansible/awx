import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { CheckIcon, CloseIcon } from '@patternfly/react-icons';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail/ErrorDetail';
import { WorkflowApprovalsAPI } from '../../../api';

function WorkflowApprovalActionButtons({
  workflowApproval,
  icon,
  i18n,
  onSuccessfulAction,
}) {
  const {
    isLoading: approveApprovalLoading,
    error: approveApprovalError,
    request: approveApprovalNode,
  } = useRequest(
    useCallback(async () => {
      await WorkflowApprovalsAPI.approve(workflowApproval.id);
      if (onSuccessfulAction) {
        onSuccessfulAction();
      }
    }, [onSuccessfulAction, workflowApproval.id]),
    {}
  );

  const {
    isLoading: denyApprovalLoading,
    error: denyApprovalError,
    request: denyApprovalNode,
  } = useRequest(
    useCallback(async () => {
      await WorkflowApprovalsAPI.deny(workflowApproval.id);
      if (onSuccessfulAction) {
        onSuccessfulAction();
      }
    }, [onSuccessfulAction, workflowApproval.id]),
    {}
  );

  const {
    error: approveError,
    dismissError: dismissApproveError,
  } = useDismissableError(approveApprovalError);

  const {
    error: denyError,
    dismissError: dismissDenyError,
  } = useDismissableError(denyApprovalError);

  return (
    <>
      <Tooltip content={i18n._(t`Approve`)} position="top">
        <Button
          isDisabled={approveApprovalLoading || denyApprovalLoading}
          aria-label={i18n._(t`Approve`)}
          variant={icon ? 'plain' : 'primary'}
          onClick={approveApprovalNode}
        >
          {icon ? <CheckIcon /> : i18n._(t`Approve`)}
        </Button>
      </Tooltip>
      <Tooltip content={i18n._(t`Deny`)} position="top">
        <Button
          isDisabled={approveApprovalLoading || denyApprovalLoading}
          aria-label={i18n._(t`Deny`)}
          variant={icon ? 'plain' : 'danger'}
          onClick={denyApprovalNode}
        >
          {icon ? <CloseIcon /> : i18n._(t`Deny`)}
        </Button>
      </Tooltip>
      {approveError && (
        <AlertModal
          isOpen={approveError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissApproveError}
        >
          {i18n._(t`Failed to approve this approval node.`)}
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
          {i18n._(t`Failed to deny this approval node.`)}
          <ErrorDetail error={denyError} />
        </AlertModal>
      )}
    </>
  );
}

WorkflowApprovalActionButtons.propTypes = {
  workflowApproval: PropTypes.shape({}).isRequired,
  icon: PropTypes.bool,
  onSuccessfulAction: PropTypes.func,
};

WorkflowApprovalActionButtons.defaultProps = {
  icon: true,
  onSuccessfulAction: () => {},
};

export default withI18n()(WorkflowApprovalActionButtons);
