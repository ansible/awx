import React from 'react';
import { t } from '@lingui/macro';
import { Label, Tooltip } from '@patternfly/react-core';
import { CheckIcon, InfoCircleIcon } from '@patternfly/react-icons';
import { WorkflowApproval } from '../../../types';
import { formatDateString } from '../../../util/dates';

function WorkflowApprovalStatus({ workflowApproval }) {
  if (workflowApproval.status === 'pending') {
    return workflowApproval.approval_expiration
      ? t`Expires on ${formatDateString(workflowApproval.approval_expiration)}`
      : t`Never expires`;
  }

  if (workflowApproval.timed_out) {
    return <Label color="red">{t`Timed out`}</Label>;
  }

  if (workflowApproval.canceled_on) {
    return <Label color="red">{t`Canceled`}</Label>;
  }

  if (workflowApproval.status === 'failed' && workflowApproval.failed) {
    return (
      <Tooltip
        content={
          workflowApproval.summary_fields?.approved_or_denied_by?.username
            ? t`Denied by ${
                workflowApproval.summary_fields.approved_or_denied_by.username
              } - ${formatDateString(workflowApproval.finished)}`
            : t`Denied - ${formatDateString(
                workflowApproval.finished
              )}.  See the Activity Stream for more information.`
        }
        position="top"
      >
        <Label variant="outline" color="red" icon={<InfoCircleIcon />}>
          {t`Denied`}
        </Label>
      </Tooltip>
    );
  }

  if (workflowApproval.status === 'successful') {
    return (
      <Tooltip
        content={
          workflowApproval.summary_fields?.approved_or_denied_by?.username
            ? t`Approved by ${
                workflowApproval.summary_fields.approved_or_denied_by.username
              } - ${formatDateString(workflowApproval.finished)}`
            : t`Approved - ${formatDateString(
                workflowApproval.finished
              )}.  See the Activity Stream for more information.`
        }
        position="top"
      >
        <Label variant="outline" color="green" icon={<CheckIcon />}>
          {t`Approved`}
        </Label>
      </Tooltip>
    );
  }

  return null;
}

WorkflowApprovalStatus.defaultProps = {
  workflowApproval: WorkflowApproval.isRequired,
};

export default WorkflowApprovalStatus;
