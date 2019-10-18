import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { RocketIcon } from '@patternfly/react-icons';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import LaunchButton from '@components/LaunchButton';
import ListActionButton from '@components/ListActionButton';
import VerticalSeparator from '@components/VerticalSeparator';
import { StatusIcon } from '@components/Sparkline';
import { toTitleCase } from '@util/strings';
import { formatDateString } from '@util/dates';
import { JOB_TYPE_URL_SEGMENTS } from '../../../constants';

const PaddedIcon = styled(StatusIcon)`
  margin-right: 20px;
`;

class JobListItem extends Component {
  render() {
    const { i18n, job, isSelected, onSelect } = this.props;

    return (
      <DataListItem
        aria-labelledby={`check-action-${job.id}`}
        css="--pf-c-data-list__expandable-content--BoxShadow: none;"
      >
        <DataListItemRow>
          <DataListCheck
            id={`select-job-${job.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={`check-action-${job.id}`}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="divider">
                <VerticalSeparator />
                {job.status && <PaddedIcon status={job.status} />}
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
              <DataListCell lastcolumn="true" key="relaunch">
                {job.type !== 'system_job' &&
                  job.summary_fields.user_capabilities.start && (
                    <Tooltip content={i18n._(t`Relaunch Job`)} position="top">
                      <LaunchButton resource={job}>
                        {({ handleRelaunch }) => (
                          <ListActionButton
                            variant="plain"
                            onClick={handleRelaunch}
                          >
                            <RocketIcon />
                          </ListActionButton>
                        )}
                      </LaunchButton>
                    </Tooltip>
                  )}
              </DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { JobListItem as _JobListItem };
export default withI18n()(JobListItem);
