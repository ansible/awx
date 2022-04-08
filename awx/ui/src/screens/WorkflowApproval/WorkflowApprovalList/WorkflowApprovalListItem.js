import React from 'react';
import { t } from '@lingui/macro';
import { string, bool, func } from 'prop-types';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import { WorkflowApproval } from 'types';
import { formatDateString } from 'util/dates';
import StatusLabel from 'components/StatusLabel';
import {
  getPendingLabel,
  getStatus,
  getTooltip,
} from '../shared/WorkflowApprovalUtils';

function WorkflowApprovalListItem({
  workflowApproval,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
}) {
  const labelId = `check-action-${workflowApproval.id}`;
  const workflowJob = workflowApproval?.summary_fields?.source_workflow_job;

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
          <b>{workflowApproval.name}</b>
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
            status={getStatus(workflowApproval)}
          />
        )}
      </Td>
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
