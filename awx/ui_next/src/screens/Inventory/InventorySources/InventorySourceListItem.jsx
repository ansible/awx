import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import {
  ExclamationTriangleIcon as PFExclamationTriangleIcon,
  PencilAltIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';

import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import StatusIcon from '../../../components/StatusIcon';
import JobCancelButton from '../../../components/JobCancelButton';
import InventorySourceSyncButton from '../shared/InventorySourceSyncButton';
import { formatDateString } from '../../../util/dates';

const ExclamationTriangleIcon = styled(PFExclamationTriangleIcon)`
  color: var(--pf-global--warning-color--100);
  margin-left: 18px;
`;

function InventorySourceListItem({
  source,
  isSelected,
  onSelect,
  detailUrl,
  label,
  rowIndex,
}) {
  const generateLastJobTooltip = job => {
    return (
      <>
        <div>{t`MOST RECENT SYNC`}</div>
        <div>
          {t`JOB ID:`} {job.id}
        </div>
        <div>
          {t`STATUS:`} {job.status.toUpperCase()}
        </div>
        {job.finished && (
          <div>
            {t`FINISHED:`} {formatDateString(job.finished)}
          </div>
        )}
      </>
    );
  };

  const missingExecutionEnvironment =
    source.custom_virtualenv && !source.execution_environment;

  return (
    <>
      <Tr id={`source-row-${source.id}`}>
        <Td
          data-cy={`check-action-${source.id}`}
          select={{
            rowIndex,
            isSelected,
            onSelect,
          }}
        />
        <Td dataLabel={t`Name`}>
          <Link to={`${detailUrl}/details`}>
            <b>{source.name}</b>
          </Link>
          {missingExecutionEnvironment && (
            <span>
              <Tooltip
                className="missing-execution-environment"
                content={t`Custom virtual environment ${source.custom_virtualenv} must be replaced by an execution environment.`}
                position="right"
              >
                <ExclamationTriangleIcon />
              </Tooltip>
            </span>
          )}
        </Td>
        <Td dataLabel={t`Status`}>
          {source.summary_fields.last_job && (
            <Tooltip
              position="top"
              content={generateLastJobTooltip(source.summary_fields.last_job)}
              key={source.summary_fields.last_job.id}
            >
              <Link to={`/jobs/inventory/${source.summary_fields.last_job.id}`}>
                <StatusIcon status={source.summary_fields.last_job.status} />
              </Link>
            </Tooltip>
          )}
        </Td>
        <Td dataLabel={t`Type`}>{label}</Td>
        <ActionsTd dataLabel={t`Actions`}>
          {['running', 'pending', 'waiting'].includes(source?.status) ? (
            <ActionItem visible={source.summary_fields.user_capabilities.start}>
              <JobCancelButton
                job={{
                  type: 'inventory_update',
                  id: source.summary_fields.last_job.id,
                }}
                errorTitle={t`Inventory Source Sync Error`}
                errorMessage={t`Failed to cancel Inventory Source Sync`}
                title={t`Cancel Inventory Source Sync`}
                showIconButton
              />
            </ActionItem>
          ) : (
            <ActionItem
              visible={source.summary_fields.user_capabilities.start}
              tooltip={t`Sync`}
            >
              <InventorySourceSyncButton source={source} />
            </ActionItem>
          )}
          <ActionItem
            visible={source.summary_fields.user_capabilities.edit}
            tooltip={t`Edit`}
          >
            <Button
              ouiaId={`${source.id}-edit-button`}
              aria-label={t`Edit Source`}
              variant="plain"
              component={Link}
              to={`${detailUrl}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </ActionItem>
        </ActionsTd>
      </Tr>
    </>
  );
}
export default InventorySourceListItem;
