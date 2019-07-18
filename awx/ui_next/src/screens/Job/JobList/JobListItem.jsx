import React, { Component } from 'react';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  DataListCheck,
} from '@patternfly/react-core';
import DataListCell from '@components/DataListCell';
import VerticalSeparator from '@components/VerticalSeparator';
import { toTitleCase } from '@util/strings';
import { JOB_TYPE_URL_SEGMENTS } from '../constants';

class JobListItem extends Component {
  render() {
    const { job, isSelected, onSelect } = this.props;

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
                <span>
                  <Link
                    to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}
                  >
                    <b>{job.name}</b>
                  </Link>
                </span>
              </DataListCell>,
              <DataListCell key="type">{toTitleCase(job.type)}</DataListCell>,
              <DataListCell key="finished">{job.finished}</DataListCell>,
            ]}
          />
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export { JobListItem as _JobListItem };
export default JobListItem;
