import 'styled-components/macro';
import React, { Fragment, useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { formatDateString, timeOfDay } from '../../../util/dates';
import { ProjectsAPI } from '../../../api';
import ClipboardCopyButton from '../../../components/ClipboardCopyButton';
import StatusLabel from '../../../components/StatusLabel';
import { toTitleCase } from '../../../util/strings';
import CopyButton from '../../../components/CopyButton';
import ProjectSyncButton from '../shared/ProjectSyncButton';
import { Project } from '../../../types';

const Label = styled.span`
  color: var(--pf-global--disabled-color--100);
`;

function ProjectListItem({
  project,
  isSelected,
  onSelect,
  detailUrl,
  fetchProjects,
  rowIndex,
  i18n,
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
    <Tr id={`${project.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link id={labelId} to={`${detailUrl}`}>
          <b>{project.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Status`)}>
        {project.summary_fields.last_job && (
          <Tooltip
            position="top"
            content={generateLastJobTooltip(project.summary_fields.last_job)}
            key={project.summary_fields.last_job.id}
          >
            <Link to={`/jobs/project/${project.summary_fields.last_job.id}`}>
              <StatusLabel status={project.summary_fields.last_job.status} />
            </Link>
          </Tooltip>
        )}
      </Td>
      <Td dataLabel={i18n._(t`Type`)}>
        {project.scm_type === ''
          ? i18n._(t`Manual`)
          : toTitleCase(project.scm_type)}
      </Td>
      <Td dataLabel={i18n._(t`Revision`)}>
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
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={project.summary_fields.user_capabilities.start}
          tooltip={i18n._(t`Sync Project`)}
        >
          <ProjectSyncButton projectId={project.id} />
        </ActionItem>
        <ActionItem
          visible={project.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit Project`)}
        >
          <Button
            isDisabled={isDisabled}
            aria-label={i18n._(t`Edit Project`)}
            variant="plain"
            component={Link}
            to={`/projects/${project.id}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
        <ActionItem visible={project.summary_fields.user_capabilities.copy}>
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
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}
export default withI18n()(ProjectListItem);
