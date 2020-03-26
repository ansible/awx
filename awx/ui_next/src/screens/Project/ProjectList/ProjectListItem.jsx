import React, { Fragment } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
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

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { PencilAltIcon, SyncIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import ClipboardCopyButton from '@components/ClipboardCopyButton';
import ProjectSyncButton from '../shared/ProjectSyncButton';
import StatusIcon from '@components/StatusIcon';
import { toTitleCase } from '@util/strings';
import { Project } from '@types';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(2, 40px);
`;
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
      <DataListItem
        key={project.id}
        aria-labelledby={labelId}
        id={`${project.id}`}
      >
        <DataListItemRow>
          <DataListCheck
            id={`select-project-${project.id}`}
            checked={isSelected}
            onChange={onSelect}
            aria-labelledby={labelId}
          />
          <DataListItemCells
            dataListCells={[
              <DataListCell key="status" isFilled={false}>
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
              </DataListCell>,
              <DataListCell key="name">
                <Link id={labelId} to={`${detailUrl}`}>
                  <b>{project.name}</b>
                </Link>
              </DataListCell>,
              <DataListCell key="type">
                {project.scm_type === ''
                  ? i18n._(t`Manual`)
                  : toTitleCase(project.scm_type)}
              </DataListCell>,
              <DataListCell key="revision">
                {project.scm_revision.substring(0, 7)}
                {project.scm_revision ? (
                  <ClipboardCopyButton
                    stringToCopy={project.scm_revision}
                    hoverTip={i18n._(t`Copy full revision to clipboard.`)}
                    clickTip={i18n._(t`Successfully copied to clipboard!`)}
                  />
                ) : null}
              </DataListCell>,
            ]}
          />
          <DataListAction
            aria-label="actions"
            aria-labelledby={labelId}
            id={labelId}
          >
            {project.summary_fields.user_capabilities.start ? (
              <Tooltip content={i18n._(t`Sync Project`)} position="top">
                <ProjectSyncButton projectId={project.id}>
                  {handleSync => (
                    <Button
                      aria-label={i18n._(t`Sync Project`)}
                      css="grid-column: 1"
                      variant="plain"
                      onClick={handleSync}
                    >
                      <SyncIcon />
                    </Button>
                  )}
                </ProjectSyncButton>
              </Tooltip>
            ) : (
              ''
            )}
            {project.summary_fields.user_capabilities.edit ? (
              <Tooltip content={i18n._(t`Edit Project`)} position="top">
                <Button
                  aria-label={i18n._(t`Edit Project`)}
                  css="grid-column: 2"
                  variant="plain"
                  component={Link}
                  to={`/projects/${project.id}/edit`}
                >
                  <PencilAltIcon />
                </Button>
              </Tooltip>
            ) : (
              ''
            )}
          </DataListAction>
        </DataListItemRow>
      </DataListItem>
    );
  }
}
export default withI18n()(ProjectListItem);
