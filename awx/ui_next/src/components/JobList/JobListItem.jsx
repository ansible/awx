import React, { useState } from 'react';
import { Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button, Chip } from '@patternfly/react-core';
import { Tr, Td, ExpandableRowContent } from '@patternfly/react-table';
import { RocketIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { ActionsTd, ActionItem } from '../PaginatedTable';
import { LaunchButton, ReLaunchDropDown } from '../LaunchButton';
import StatusLabel from '../StatusLabel';
import { DetailList, Detail, LaunchedByDetail } from '../DetailList';
import ChipGroup from '../ChipGroup';
import CredentialChip from '../CredentialChip';
import ExecutionEnvironmentDetail from '../ExecutionEnvironmentDetail';
import { formatDateString } from '../../util/dates';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';
import JobCancelButton from '../JobCancelButton';

const Dash = styled.span``;
function JobListItem({
  job,
  rowIndex,
  isSelected,
  onSelect,
  showTypeColumn = false,
  isSuperUser = false,
}) {
  const labelId = `check-action-${job.id}`;
  const [isExpanded, setIsExpanded] = useState(false);

  const jobTypes = {
    project_update: t`Source Control Update`,
    inventory_update: t`Inventory Sync`,
    job: t`Playbook Run`,
    ad_hoc_command: t`Command`,
    system_job: t`Management Job`,
    workflow_job: t`Workflow Job`,
  };

  const {
    credentials,
    execution_environment,
    inventory,
    job_template,
    labels,
    project,
    source_workflow_job,
    workflow_job_template,
  } = job.summary_fields;

  return (
    <>
      <Tr id={`job-row-${job.id}`}>
        <Td
          expand={{
            rowIndex: job.id,
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
          dataLabel={t`Select`}
        />
        <Td id={labelId} dataLabel={t`Name`}>
          <span>
            <Link to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}>
              <b>
                {job.id} <Dash>&mdash;</Dash> {job.name}
              </b>
            </Link>
          </span>
        </Td>
        <Td dataLabel={t`Status`}>
          {job.status && <StatusLabel status={job.status} />}
        </Td>
        {showTypeColumn && <Td dataLabel={t`Type`}>{jobTypes[job.type]}</Td>}
        <Td dataLabel={t`Start Time`}>{formatDateString(job.started)}</Td>
        <Td dataLabel={t`Finish Time`}>
          {job.finished ? formatDateString(job.finished) : ''}
        </Td>
        <ActionsTd dataLabel={t`Actions`}>
          <ActionItem
            visible={
              ['pending', 'waiting', 'running'].includes(job.status) &&
              (job.type === 'system_job' ? isSuperUser : true)
            }
          >
            <JobCancelButton
              job={job}
              errorTitle={t`Job Cancel Error`}
              title={t`Cancel ${job.name}`}
              errorMessage={t`Failed to cancel ${job.name}`}
              showIconButton
            />
          </ActionItem>
          <ActionItem
            visible={
              job.type !== 'system_job' &&
              job.summary_fields?.user_capabilities?.start
            }
            tooltip={
              job.status === 'failed' && job.type === 'job'
                ? t`Relaunch using host parameters`
                : t`Relaunch Job`
            }
          >
            {job.status === 'failed' && job.type === 'job' ? (
              <LaunchButton resource={job}>
                {({ handleRelaunch, isLaunching }) => (
                  <ReLaunchDropDown
                    handleRelaunch={handleRelaunch}
                    isLaunching={isLaunching}
                  />
                )}
              </LaunchButton>
            ) : (
              <LaunchButton resource={job}>
                {({ handleRelaunch, isLaunching }) => (
                  <Button
                    ouiaId={`${job.id}-relaunch-button`}
                    variant="plain"
                    onClick={handleRelaunch}
                    aria-label={t`Relaunch`}
                    isDisabled={isLaunching}
                  >
                    <RocketIcon />
                  </Button>
                )}
              </LaunchButton>
            )}
          </ActionItem>
        </ActionsTd>
      </Tr>
      <Tr isExpanded={isExpanded} id={`expanded-job-row-${job.id}`}>
        <Td colSpan={2} />
        <Td colSpan={showTypeColumn ? 6 : 5}>
          <ExpandableRowContent>
            <DetailList>
              <LaunchedByDetail job={job} />
              {job_template && (
                <Detail
                  label={t`Job Template`}
                  value={
                    <Link to={`/templates/job_template/${job_template.id}`}>
                      {job_template.name}
                    </Link>
                  }
                />
              )}
              {workflow_job_template && (
                <Detail
                  label={t`Workflow Job Template`}
                  value={
                    <Link
                      to={`/templates/workflow_job_template/${workflow_job_template.id}`}
                    >
                      {workflow_job_template.name}
                    </Link>
                  }
                />
              )}
              {source_workflow_job && (
                <Detail
                  label={t`Source Workflow Job`}
                  value={
                    <Link to={`/jobs/workflow/${source_workflow_job.id}`}>
                      {source_workflow_job.id} - {source_workflow_job.name}
                    </Link>
                  }
                />
              )}
              {inventory && (
                <Detail
                  label={t`Inventory`}
                  value={
                    <Link
                      to={
                        inventory.kind === 'smart'
                          ? `/inventories/smart_inventory/${inventory.id}`
                          : `/inventories/inventory/${inventory.id}`
                      }
                    >
                      {inventory.name}
                    </Link>
                  }
                />
              )}
              {project && (
                <Detail
                  label={t`Project`}
                  value={
                    <Link to={`/projects/${project.id}/details`}>
                      {project.name}
                    </Link>
                  }
                  dataCy={`job-${job.id}-project`}
                />
              )}
              <ExecutionEnvironmentDetail
                virtualEnvironment={job.custom_virtualenv}
                executionEnvironment={execution_environment}
              />
              {credentials && credentials.length > 0 && (
                <Detail
                  fullWidth
                  label={t`Credentials`}
                  value={
                    <ChipGroup numChips={5} totalChips={credentials.length}>
                      {credentials.map(c => (
                        <CredentialChip key={c.id} credential={c} isReadOnly />
                      ))}
                    </ChipGroup>
                  }
                />
              )}
              {labels && labels.count > 0 && (
                <Detail
                  fullWidth
                  label={t`Labels`}
                  value={
                    <ChipGroup numChips={5} totalChips={labels.results.length}>
                      {labels.results.map(l => (
                        <Chip key={l.id} isReadOnly>
                          {l.name}
                        </Chip>
                      ))}
                    </ChipGroup>
                  }
                />
              )}
              {job.job_explanation && (
                <Detail
                  fullWidth
                  label={t`Explanation`}
                  value={job.job_explanation}
                />
              )}
            </DetailList>
          </ExpandableRowContent>
        </Td>
      </Tr>
    </>
  );
}

export { JobListItem as _JobListItem };
export default JobListItem;
