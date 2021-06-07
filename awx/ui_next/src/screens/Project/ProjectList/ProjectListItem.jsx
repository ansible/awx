import 'styled-components/macro';
import React, { Fragment, useState, useCallback } from 'react';
import { string, bool, func } from 'prop-types';

import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td, ExpandableRowContent } from '@patternfly/react-table';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  PencilAltIcon,
  ExclamationTriangleIcon as PFExclamationTriangleIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { formatDateString, timeOfDay } from '../../../util/dates';
import { ProjectsAPI } from '../../../api';
import ClipboardCopyButton from '../../../components/ClipboardCopyButton';
import {
  DetailList,
  Detail,
  DeletedDetail,
} from '../../../components/DetailList';
import ExecutionEnvironmentDetail from '../../../components/ExecutionEnvironmentDetail';
import StatusLabel from '../../../components/StatusLabel';
import { toTitleCase } from '../../../util/strings';
import CopyButton from '../../../components/CopyButton';
import ProjectSyncButton from '../shared/ProjectSyncButton';
import { Project } from '../../../types';
import JobCancelButton from '../../../components/JobCancelButton';

const Label = styled.span`
  color: var(--pf-global--disabled-color--100);
`;

const ExclamationTriangleIcon = styled(PFExclamationTriangleIcon)`
  color: var(--pf-global--warning-color--100);
  margin-left: 18px;
`;

function ProjectListItem({
  project,
  isSelected,
  onSelect,
  detailUrl,
  fetchProjects,
  rowIndex,
}) {
  const [isExpanded, setIsExpanded] = useState(false);
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

  const missingExecutionEnvironment =
    project.custom_virtualenv && !project.default_environment;

  let job = null;

  if (project.summary_fields?.current_job) {
    job = project.summary_fields.current_job;
  } else if (project.summary_fields?.last_job) {
    job = project.summary_fields.last_job;
  }

  return (
    <>
      <Tr id={`${project.id}`}>
        <Td
          expand={{
            rowIndex,
            isExpanded,
            onToggle: () => setIsExpanded(!isExpanded),
          }}
        />
        <Td
          select={{
            rowIndex,
            isSelected,
            onSelect,
          }}
          dataLabel={t`Selected`}
        />
        <Td id={labelId} dataLabel={t`Name`}>
          <span>
            <Link to={`${detailUrl}`}>
              <b>{project.name}</b>
            </Link>
          </span>
          {missingExecutionEnvironment && (
            <span>
              <Tooltip
                content={t`Custom virtual environment ${project.custom_virtualenv} must be replaced by an execution environment.`}
                position="right"
                className="missing-execution-environment"
              >
                <ExclamationTriangleIcon />
              </Tooltip>
            </span>
          )}
        </Td>
        <Td dataLabel={t`Status`}>
          {job && (
            <Tooltip
              position="top"
              content={generateLastJobTooltip(job)}
              key={job.id}
            >
              <Link to={`/jobs/project/${job.id}`}>
                <StatusLabel status={job.status} />
              </Link>
            </Tooltip>
          )}
        </Td>
        <Td dataLabel={t`Type`}>
          {project.scm_type === '' ? t`Manual` : toTitleCase(project.scm_type)}
        </Td>
        <Td dataLabel={t`Revision`}>
          {project.scm_revision.substring(0, 7)}
          {!project.scm_revision && (
            <Label aria-label={t`copy to clipboard disabled`}>
              {t`Sync for revision`}
            </Label>
          )}
          <ClipboardCopyButton
            isDisabled={!project.scm_revision}
            stringToCopy={project.scm_revision}
            copyTip={t`Copy full revision to clipboard.`}
            copiedSuccessTip={t`Successfully copied to clipboard!`}
            ouiaId="copy-revision-button"
          />
        </Td>
        <ActionsTd dataLabel={t`Actions`}>
          {['running', 'pending', 'waiting'].includes(job?.status) ? (
            <ActionItem
              visible={project.summary_fields.user_capabilities.start}
            >
              <JobCancelButton
                job={{ id: job.id, type: 'project_update' }}
                errorTitle={t`Project Sync Error`}
                title={t`Cancel Project Sync`}
                showIconButton
                errorMessage={t`Failed to cancel Project Sync`}
              />
            </ActionItem>
          ) : (
            <ActionItem
              visible={project.summary_fields.user_capabilities.start}
              tooltip={t`Sync Project`}
            >
              <ProjectSyncButton
                projectId={project.id}
                lastJobStatus={job && job.status}
              />
            </ActionItem>
          )}
          <ActionItem
            visible={project.summary_fields.user_capabilities.edit}
            tooltip={t`Edit Project`}
          >
            <Button
              ouiaId={`${project.id}-edit-button`}
              isDisabled={isDisabled}
              aria-label={t`Edit Project`}
              variant="plain"
              component={Link}
              to={`/projects/${project.id}/edit`}
            >
              <PencilAltIcon />
            </Button>
          </ActionItem>
          <ActionItem
            tooltip={t`Copy Project`}
            visible={project.summary_fields.user_capabilities.copy}
          >
            <CopyButton
              copyItem={copyProject}
              isDisabled={isDisabled}
              onCopyStart={handleCopyStart}
              onCopyFinish={handleCopyFinish}
              errorMessage={t`Failed to copy project.`}
            />
          </ActionItem>
        </ActionsTd>
      </Tr>
      <Tr isExpanded={isExpanded} id={`expanded-project-row-${project.id}`}>
        <Td colSpan={2} />
        <Td colSpan={5}>
          <ExpandableRowContent>
            <DetailList>
              <Detail
                label={t`Description`}
                value={project.description}
                dataCy={`project-${project.id}-description`}
              />
              {project.summary_fields.organization ? (
                <Detail
                  label={t`Organization`}
                  value={
                    <Link
                      to={`/organizations/${project.summary_fields.organization.id}/details`}
                    >
                      {project.summary_fields.organization.name}
                    </Link>
                  }
                  dataCy={`project-${project.id}-organization`}
                />
              ) : (
                <DeletedDetail label={t`Organization`} />
              )}
              <ExecutionEnvironmentDetail
                virtualEnvironment={project.custom_virtualenv}
                executionEnvironment={
                  project.summary_fields?.default_environment
                }
                isDefaultEnvironment
              />
              <Detail
                label={t`Last modified`}
                value={formatDateString(project.modified)}
                dataCy={`project-${project.id}-last-modified`}
              />
              <Detail
                label={t`Last used`}
                value={formatDateString(project.last_job_run)}
                dataCy={`project-${project.id}-last-used`}
              />
            </DetailList>
          </ExpandableRowContent>
        </Td>
      </Tr>
    </>
  );
}
export default ProjectListItem;
