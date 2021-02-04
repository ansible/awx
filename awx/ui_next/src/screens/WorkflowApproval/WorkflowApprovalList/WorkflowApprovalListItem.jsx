import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { string, bool, func } from 'prop-types';
import { Label } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { WorkflowApproval } from '../../../types';
import { formatDateString } from '../../../util/dates';
import WorkflowApprovalStatus from '../shared/WorkflowApprovalStatus';

const JobLabel = styled.b`
  margin-right: 24px;
`;

function WorkflowApprovalListItem({
  workflowApproval,
  isSelected,
  onSelect,
  detailUrl,
  rowIndex,
  i18n,
}) {
  const labelId = `check-action-${workflowApproval.id}`;
  const workflowJob = workflowApproval?.summary_fields?.source_workflow_job;

  const getStatus = () => {
    if (
      workflowApproval.status === 'pending' &&
      workflowApproval.approval_expiration
    ) {
      return (
        <Label>
          {i18n._(
            t`Expires on ${formatDateString(
              workflowApproval.approval_expiration
            )}`
          )}
        </Label>
      );
    }
    if (
      workflowApproval.status === 'pending' &&
      !workflowApproval.approval_expiration
    ) {
      return <Label>{i18n._(t`Never expires`)}</Label>;
    }
    return <WorkflowApprovalStatus workflowApproval={workflowApproval} />;
  };

  return (
    <Tr id={`workflow-approval-row-${workflowApproval.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${detailUrl}`}>
          <b>{workflowApproval.name}</b>
        </Link>
      </Td>
      <Td>
        <>
          <JobLabel>{i18n._(t`Job`)}</JobLabel>
          {workflowJob && workflowJob?.id ? (
            <Link to={`/jobs/workflow/${workflowJob?.id}`}>
              {`${workflowJob?.id} - ${workflowJob?.name}`}
            </Link>
          ) : (
            i18n._(t`Deleted`)
          )}
        </>
      </Td>
      <Td dataLabel={i18n._(t`Started`)}>
        {formatDateString(workflowApproval.started)}
      </Td>
      <Td dataLabel={i18n._(t`Status`)}>
        <div>{getStatus()}</div>
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

export default withI18n()(WorkflowApprovalListItem);
