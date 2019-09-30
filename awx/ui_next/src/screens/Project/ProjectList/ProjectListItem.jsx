import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { Link as _Link } from 'react-router-dom';
import { SyncIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import ProjectSyncButton from '../shared/ProjectSyncButton';
import { StatusIcon } from '@components/Sparkline';
import VerticalSeparator from '@components/VerticalSeparator';
import { Project } from '@types';

/* eslint-disable react/jsx-pascal-case */
const Link = styled(props => <_Link {...props} />)`
  margin-right: 10px;
`;
/* eslint-enable react/jsx-pascal-case */

class ProjectListItem extends React.Component {
  static propTypes = {
    project: Project.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  constructor(props) {
    super(props);

    this.generateLastJobTooltip = this.generateLastJobTooltip.bind(this);
  }

  generateLastJobTooltip = job => {
    const { i18n } = this.props;
    return (
      <Fragment>
        <div>{i18n._(t`MOST RECENT SYNC`)}</div>
        <div>
          {i18n._(t`JOB ID:`)} {job.id}
        </div>
        <div>
          {i18n._(t`STATUS:`)} {job.status.toUpperCase()}
        </div>
        {job.finished && (
          <div>
            {i18n._(t`FINISHED:`)} {job.finished}
          </div>
        )}
      </Fragment>
    );
  };

  render() {
    const { project, isSelected, onSelect, detailUrl, i18n } = this.props;
    const labelId = `check-action-${project.id}`;
    return (
      <DataListItem key={project.id} aria-labelledby={labelId}>
        <DataListItemRow>
          <DataListCheck
            id={`select-project-${project.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="divider">
                <VerticalSeparator />
                {project.summary_fields.last_job && (
                  <Tooltip
                    position="top"
                    content={this.generateLastJobTooltip(
                      project.summary_fields.last_job
                    )}
                    key={project.summary_fields.last_job.id}
                  >
                    <Link
                      to={`/jobs/project/${project.summary_fields.last_job.id}`}
                    >
                      <StatusIcon
                        status={project.summary_fields.last_job.status}
                      />
                    </Link>
                  </Tooltip>
                )}
                <span id={labelId}>
                  <Link to={`${detailUrl}`}>
                    <b>{project.name}</b>
                  </Link>
                </span>
              </DataListCell>,
              <DataListCell key="type">
                {project.scm_type.toUpperCase()}
              </DataListCell>,
              <DataListCell lastcolumn="true" key="action">
                {project.summary_fields.user_capabilities.start && (
                  <Tooltip content={i18n._(t`Sync Project`)} position="top">
                    <ProjectSyncButton projectId={project.id}>
                      {handleSync => (
                        <ListActionButton variant="plain" onClick={handleSync}>
                          <SyncIcon />
                        </ListActionButton>
                      )}
                    </ProjectSyncButton>
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
export default withI18n()(ProjectListItem);
