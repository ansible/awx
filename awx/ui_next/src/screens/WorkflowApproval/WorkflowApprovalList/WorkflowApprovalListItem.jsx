import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { string, bool, func } from 'prop-types';
import {
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Label,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import DataListCell from '../../../components/DataListCell';
import { WorkflowApproval } from '../../../types';
import { formatDateString } from '../../../util/dates';
import WorkflowApprovalStatus from '../shared/WorkflowApprovalStatus';

const StatusCell = styled(DataListCell)`
  @media screen and (min-width: 768px) {
    display: flex;
    justify-content: flex-end;
  }
`;

const JobLabel = styled.b`
  margin-right: 24px;
`;

function WorkflowApprovalListItem({
  workflowApproval,
  isSelected,
  onSelect,
  detailUrl,
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
    <DataListItem
      key={workflowApproval.id}
      aria-labelledby={labelId}
      id={`${workflowApproval.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-workflowApproval-${workflowApproval.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="title">
              <Link to={`${detailUrl}`}>
                <b>{workflowApproval.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="job">
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
            </DataListCell>,
            <StatusCell key="status">
              <div>{getStatus()}</div>
            </StatusCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

WorkflowApprovalListItem.propTypes = {
  workflowApproval: WorkflowApproval.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(WorkflowApprovalListItem);
