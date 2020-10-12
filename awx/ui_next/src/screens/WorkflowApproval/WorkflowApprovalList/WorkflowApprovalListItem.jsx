import React, { useCallback, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { string, bool, func } from 'prop-types';
import {
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
} from '@patternfly/react-core';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import DataListCell from '../../../components/DataListCell';
import { WorkflowApproval } from '../../../types';
import { formatDateString } from '../../../util/dates';
import WorkflowApprovalActionButtons from '../shared/WorkflowApprovalActionButtons';
import WorkflowApprovalStatus from '../shared/WorkflowApprovalStatus';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(2, 40px);
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
  const [actionTaken, setActionTaken] = useState(false);
  const labelId = `check-action-${workflowApproval.id}`;
  const workflowJob = workflowApproval?.summary_fields?.source_workflow_job;

  const getStatus = () => {
    if (
      workflowApproval.status === 'pending' &&
      workflowApproval.approval_expiration
    ) {
      return i18n._(
        t`Expires on ${formatDateString(workflowApproval.approval_expiration)}`
      );
    }
    if (
      workflowApproval.status === 'pending' &&
      !workflowApproval.approval_expiration
    ) {
      return i18n._(t`Never expires`);
    }
    return <WorkflowApprovalStatus workflowApproval={workflowApproval} />;
  };

  const handleSuccesfulAction = useCallback(() => {
    setActionTaken(true);
  }, []);

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
            <DataListCell key="title" id={labelId}>
              <Link to={`${detailUrl}`}>
                <b>{workflowApproval.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="job" id={labelId}>
              {workflowJob && (
                <>
                  <JobLabel>{i18n._(t`Job`)}</JobLabel>
                  <Link to={`/jobs/workflow/${workflowJob?.id}`}>
                    {`${workflowJob?.id} - ${workflowJob?.name}`}
                  </Link>
                </>
              )}
            </DataListCell>,
            <DataListCell key="status">{getStatus()}</DataListCell>,
          ]}
        />
        <DataListAction aria-label="actions" aria-labelledby={labelId}>
          {workflowApproval.can_approve_or_deny && !actionTaken ? (
            <WorkflowApprovalActionButtons
              workflowApproval={workflowApproval}
              onSuccessfulAction={handleSuccesfulAction}
            />
          ) : (
            ''
          )}
        </DataListAction>
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
