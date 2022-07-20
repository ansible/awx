import React from 'react';
import { t } from '@lingui/macro';
import { string, bool, func } from 'prop-types';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { WorkflowApproval } from 'types';
import { formatDateString } from 'util/dates';
import StatusLabel from 'components/StatusLabel';
import JobCancelButton from 'components/JobCancelButton';
import { ActionItem, ActionsTd } from 'components/PaginatedTable';
import {
  getPendingLabel,
  getStatus,
  getTooltip,
} from '../shared/WorkflowApprovalUtils';
import WorkflowApprovalButton from '../shared/WorkflowApprovalButton';
import WorkflowDenyButton from '../shared/WorkflowDenyButton';

function WorkflowApprovalListItem({
  workflowApproval,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
}) {
  const hasBeenActedOn =
    workflowApproval.status === 'successful' ||
    workflowApproval.status === 'failed' ||
    workflowApproval.status === 'canceled';
  const labelId = `check-action-${workflowApproval.id}`;
  const workflowJob = workflowApproval?.summary_fields?.source_workflow_job;
  const status = getStatus(workflowApproval);
  return (
    <Tr id={`workflow-approval-row-${workflowApproval.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={t`Selected`}
      />
      <Td id={labelId} dataLabel={t`Name`}>
        <Link to={`${detailUrl}`}>
          {workflowJob && workflowJob?.id ? (
            <b>{`${workflowJob?.id} - ${workflowApproval?.name}`}</b>
          ) : (
            <b>
              {t`Deleted`} {`- ${workflowApproval?.name}`}
            </b>
          )}
        </Link>
      </Td>
      <Td>
        {workflowJob && workflowJob?.id ? (
          <Link to={`/jobs/workflow/${workflowJob?.id}`}>
            {`${workflowJob?.id} - ${workflowJob?.name}`}
          </Link>
        ) : (
          t`Deleted`
        )}
      </Td>
      <Td dataLabel={t`Started`}>
        {formatDateString(workflowApproval.started)}
      </Td>
      <Td dataLabel={t`Status`}>
        {workflowApproval.status === 'pending' ? (
          <StatusLabel status={workflowApproval.status}>
            {getPendingLabel(workflowApproval)}
          </StatusLabel>
        ) : (
          <StatusLabel
            tooltipContent={getTooltip(workflowApproval)}
            status={status}
          />
        )}
      </Td>
      <ActionsTd dataLabel={t`Actions`}>
        <ActionItem
          visible
          tooltip={
            hasBeenActedOn
              ? t`This workflow has already been ${status}`
              : t`Approve`
          }
        >
          <WorkflowApprovalButton workflowApproval={workflowApproval} />
        </ActionItem>
        <ActionItem
          visible
          tooltip={
            hasBeenActedOn
              ? t`This workflow has already been ${status}`
              : t`Deny`
          }
        >
          <WorkflowDenyButton workflowApproval={workflowApproval} />
        </ActionItem>
        <ActionItem visible>
          <JobCancelButton
            title={t`Cancel Workflow`}
            showIconButton
            job={workflowApproval.summary_fields.source_workflow_job}
            buttonText={t`Cancel Workflow`}
            isDisabled={hasBeenActedOn}
            tooltip={
              hasBeenActedOn
                ? t`This workflow has already been ${status}`
                : t`Cancel`
            }
            cancelationMessage={t`This will cancel all subsequent nodes in this workflow
            `}
          />
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

WorkflowApprovalListItem.propTypes = {
  workflowApproval: WorkflowApproval.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default WorkflowApprovalListItem;
