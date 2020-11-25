import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Label, Tooltip } from '@patternfly/react-core';
import { CheckIcon, InfoCircleIcon } from '@patternfly/react-icons';
import { WorkflowApproval } from '../../../types';
import { formatDateString } from '../../../util/dates';

function WorkflowApprovalStatus({ workflowApproval, i18n }) {
  if (workflowApproval.status === 'pending') {
    return workflowApproval.approval_expiration
      ? i18n._(
          t`Expires on ${formatDateString(
            workflowApproval.approval_expiration
          )}`
        )
      : i18n._(t`Never expires`);
  }

  if (workflowApproval.timed_out) {
    return <Label color="red">{i18n._(t`Timed out`)}</Label>;
  }

  if (workflowApproval.canceled_on) {
    return <Label color="red">{i18n._(t`Canceled`)}</Label>;
  }

  if (workflowApproval.status === 'failed' && workflowApproval.failed) {
    return (
      <Tooltip
        content={i18n._(
          t`Denied by ${
            workflowApproval.summary_fields.approved_or_denied_by.username
          } - ${formatDateString(workflowApproval.finished)}`
        )}
        position="top"
      >
        <Label variant="outline" color="red" icon={<InfoCircleIcon />}>
          {i18n._(t`Denied`)}
        </Label>
      </Tooltip>
    );
  }

  if (workflowApproval.status === 'successful') {
    return (
      <Tooltip
        content={i18n._(
          t`Approved by ${
            workflowApproval.summary_fields.approved_or_denied_by.username
          } - ${formatDateString(workflowApproval.finished)}`
        )}
        position="top"
      >
        <Label variant="outline" color="green" icon={<CheckIcon />}>
          {i18n._(t`Approved`)}
        </Label>
      </Tooltip>
    );
  }

  return null;
}

WorkflowApprovalStatus.defaultProps = {
  workflowApproval: WorkflowApproval.isRequired,
};

export default withI18n()(WorkflowApprovalStatus);
