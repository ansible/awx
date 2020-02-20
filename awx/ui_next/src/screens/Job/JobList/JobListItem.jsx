import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  DataListAction,
  DataListCell,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { RocketIcon } from '@patternfly/react-icons';
import LaunchButton from '@components/LaunchButton';
import StatusIcon from '@components/StatusIcon';
import { toTitleCase } from '@util/strings';
import { formatDateString } from '@util/dates';
import { JOB_TYPE_URL_SEGMENTS } from '@constants';

class JobListItem extends Component {
  render() {
    const { i18n, job, isSelected, onSelect } = this.props;
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
              <DataListCell key="name" css="display: inline-flex;">
                <span>
                  <Link
                    to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}
                  >
                    <b>
                      {job.id} &mdash; {job.name}
                    </b>
                  </Link>
                </span>
              </DataListCell>,
              <DataListCell key="type">{toTitleCase(job.type)}</DataListCell>,
              <DataListCell key="finished">
                {formatDateString(job.finished)}
              </DataListCell>,
            ]}
          />
          {job.type !== 'system_job' &&
            job.summary_fields?.user_capabilities?.start && (
              <DataListAction
                aria-label="actions"
                aria-labelledby={labelId}
                id={labelId}
              >
                <Tooltip content={i18n._(t`Relaunch Job`)} position="top">
                  <LaunchButton resource={job}>
                    {({ handleRelaunch }) => (
                      <Button variant="plain" onClick={handleRelaunch}>
                        <RocketIcon />
                      </Button>
                    )}
                  </LaunchButton>
                </Tooltip>
              </DataListAction>
            )}
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { JobListItem as _JobListItem };
export default withI18n()(JobListItem);
