import React from 'react';

import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Button,
  DataListItem,
  DataListItemRow,
  DataListCheck,
  DataListItemCells,
  DataListCell,
  DataListAction,
  Tooltip,
} from '@patternfly/react-core';
import {
  ExclamationTriangleIcon as PFExclamationTriangleIcon,
  PencilAltIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';

import StatusIcon from '../../../components/StatusIcon';
import InventorySourceSyncButton from '../shared/InventorySourceSyncButton';

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
            {t`FINISHED:`} {job.finished}
          </div>
        )}
      </>
    );
  };

  const missingExecutionEnvironment =
    source.custom_virtualenv && !source.execution_environment;

  return (
    <>
      <DataListItem aria-labelledby={`check-action-${source.id}`}>
        <DataListItemRow>
          <DataListCheck
            id={`select-source-${source.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={`check-action-${source.id}`}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="status" isFilled={false}>
                {source.summary_fields.last_job && (
                  <Tooltip
                    position="top"
                    content={generateLastJobTooltip(
                      source.summary_fields.last_job
                    )}
                    key={source.summary_fields.last_job.id}
                  >
                    <Link
                      to={`/jobs/inventory/${source.summary_fields.last_job.id}`}
                    >
                      <StatusIcon
                        status={source.summary_fields.last_job.status}
                      />
                    </Link>
                  </Tooltip>
                )}
              </DataListCell>,
              <DataListCell aria-label={t`name`} key="name">
                <span>
                  <Link to={`${detailUrl}/details`}>
                    <b>{source.name}</b>
                  </Link>
                </span>
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
              </DataListCell>,
              <DataListCell aria-label={t`type`} key="type">
                {label}
              </DataListCell>,
            ]}
          />
          <DataListAction
            id="actions"
            aria-labelledby="actions"
            aria-label={t`actions`}
          >
            {source.summary_fields.user_capabilities.start && (
              <InventorySourceSyncButton source={source} />
            )}
            {source.summary_fields.user_capabilities.edit && (
              <Button
                ouiaId={`${source.id}-edit-button`}
                aria-label={t`Edit Source`}
                variant="plain"
                component={Link}
                to={`${detailUrl}/edit`}
              >
                <PencilAltIcon />
              </Button>
            )}
          </DataListAction>
        </DataListItemRow>
      </DataListItem>
    </>
  );
}
export default InventorySourceListItem;
