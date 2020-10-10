import 'styled-components/macro';
import React, { Fragment, useState, useCallback } from 'react';
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

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { PencilAltIcon, SyncIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { formatDateString, timeOfDay } from '../../../util/dates';
import { ProjectsAPI } from '../../../api';
import ClipboardCopyButton from '../../../components/ClipboardCopyButton';
import StatusIcon from '../../../components/StatusIcon';
import DataListCell from '../../../components/DataListCell';
import { toTitleCase } from '../../../util/strings';
import CopyButton from '../../../components/CopyButton';
import ProjectSyncButton from '../shared/ProjectSyncButton';
import { Project } from '../../../types';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: repeat(3, 40px);
`;

const Label = styled.span`
  color: var(--pf-global--disabled-color--100);
`;

function ProjectListItem({
  project,
  isSelected,
  onSelect,
  detailUrl,
  i18n,
  fetchProjects,
}) {
  const [isDisabled, setIsDisabled] = useState(false);
  ProjectListItem.propTypes = {
    project: Project.isRequired,
    detailUrl: string.isRequired,
    isSelected: bool.isRequired,
    onSelect: func.isRequired,
  };

  const copyProject = useCallback(async () => {
    await ProjectsAPI.copy(project.id, {
      name: `${project.name} @ ${timeOfDay()}`,
    });
    await fetchProjects();
  }, [project.id, project.name, fetchProjects]);

  const generateLastJobTooltip = job => {
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
            {i18n._(t`FINISHED:`)} {formatDateString(job.finished)}
          </div>
        )}
      </Fragment>
    );
  };

  const handleCopyStart = useCallback(() => {
    setIsDisabled(true);
  }, []);

  const handleCopyFinish = useCallback(() => {
    setIsDisabled(false);
  }, []);

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
                  content={generateLastJobTooltip(
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
              {!project.scm_revision && (
                <Label aria-label={i18n._(t`copy to clipboard disabled`)}>
                  {i18n._(t`Sync for revision`)}
                </Label>
              )}
              <ClipboardCopyButton
                isDisabled={!project.scm_revision}
                stringToCopy={project.scm_revision}
                copyTip={i18n._(t`Copy full revision to clipboard.`)}
                copiedSuccessTip={i18n._(t`Successfully copied to clipboard!`)}
              />
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
                    isDisabled={isDisabled}
                    aria-label={i18n._(t`Sync Project`)}
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
                isDisabled={isDisabled}
                aria-label={i18n._(t`Edit Project`)}
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
          {project.summary_fields.user_capabilities.copy && (
            <CopyButton
              copyItem={copyProject}
              isDisabled={isDisabled}
              onCopyStart={handleCopyStart}
              onCopyFinish={handleCopyFinish}
              helperText={{
                tooltip: i18n._(t`Copy Project`),
                errorMessage: i18n._(t`Failed to copy project.`),
              }}
            />
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}
export default withI18n()(ProjectListItem);
