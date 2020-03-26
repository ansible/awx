import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';
import { RocketIcon } from '@patternfly/react-icons';
import LaunchButton from '@components/LaunchButton';
import StatusIcon from '@components/StatusIcon';
import { toTitleCase } from '@util/strings';
import { formatDateString } from '@util/dates';
import { JOB_TYPE_URL_SEGMENTS } from '@constants';
import styled from 'styled-components';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px;
`;

function JobListItem({
  i18n,
  job,
  isSelected,
  onSelect,
  showTypeColumn = false,
}) {
  const labelId = `check-action-${job.id}`;

  return (
    <DataListItem aria-labelledby={labelId} id={`${job.id}`}>
      <DataListItemRow>
        <DataListCheck
          id={`select-job-${job.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="status" isFilled={false}>
              {job.status && <StatusIcon status={job.status} />}
            </DataListCell>,
            <DataListCell key="name">
              <span>
                <Link to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}>
                  <b>
                    {job.id} &mdash; {job.name}
                  </b>
                </Link>
              </span>
            </DataListCell>,
            ...(showTypeColumn
              ? [
                  <DataListCell key="type" aria-label="type">
                    {toTitleCase(job.type)}
                  </DataListCell>,
                ]
              : []),
            <DataListCell key="finished">
              {formatDateString(job.finished)}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {job.type !== 'system_job' &&
          job.summary_fields?.user_capabilities?.start ? (
            <Tooltip content={i18n._(t`Relaunch Job`)} position="top">
              <LaunchButton resource={job}>
                {({ handleRelaunch }) => (
                  <Button
                    variant="plain"
                    onClick={handleRelaunch}
                    aria-label={i18n._(t`Relaunch`)}
                  >
                    <RocketIcon />
                  </Button>
                )}
              </LaunchButton>
            </Tooltip>
          ) : (
            ''
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

export { JobListItem as _JobListItem };
export default withI18n()(JobListItem);
