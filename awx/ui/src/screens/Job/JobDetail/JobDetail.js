import 'styled-components/macro';
import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import { Button, Chip } from '@patternfly/react-core';
import styled from 'styled-components';

import { useConfig } from 'contexts/Config';
import AlertModal from 'components/AlertModal';
import {
  DeletedDetail,
  DetailList,
  Detail,
  UserDateDetail,
  LaunchedByDetail,
} from 'components/DetailList';
import { CardBody, CardActionsRow } from 'components/Card';
import ChipGroup from 'components/ChipGroup';
import CredentialChip from 'components/CredentialChip';
import { VariablesDetail } from 'components/CodeEditor';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import { LaunchButton, ReLaunchDropDown } from 'components/LaunchButton';
import StatusLabel from 'components/StatusLabel';
import JobCancelButton from 'components/JobCancelButton';
import ExecutionEnvironmentDetail from 'components/ExecutionEnvironmentDetail';
import { getJobModel, isJobRunning } from 'util/jobs';
import { formatDateString } from 'util/dates';
import { Job } from 'types';
import jobHelpText from '../Job.helptext';

const StatusDetailValue = styled.div`
  align-items: center;
  display: inline-grid;
  grid-gap: 10px;
  grid-template-columns: auto auto;
`;

const VERBOSITY = {
  0: '0 (Normal)',
  1: '1 (Verbose)',
  2: '2 (More Verbose)',
  3: '3 (Debug)',
  4: '4 (Connection Debug)',
};

function JobDetail({ job, inventorySourceLabels }) {
  const { me } = useConfig();
  const {
    created_by,
    credential,
    credentials,
    instance_group: instanceGroup,
    inventory,
    inventory_source,
    source_project,
    job_template: jobTemplate,
    workflow_job_template: workflowJobTemplate,
    labels,
    project,
    project_update: projectUpdate,
    source_workflow_job,
    execution_environment: executionEnvironment,
  } = job.summary_fields;
  const { scm_branch: scmBranch } = job;
  const [errorMsg, setErrorMsg] = useState();
  const history = useHistory();

  const jobTypes = {
    project_update: t`Source Control Update`,
    inventory_update: t`Inventory Sync`,
    job: job.job_type === 'check' ? t`Playbook Check` : t`Playbook Run`,
    ad_hoc_command: t`Run Command`,
    system_job: t`Management Job`,
    workflow_job: t`Workflow Job`,
  };

  const scmTypes = {
    '': t`Manual`,
    git: t`Git`,
    svn: t`Subversion`,
    insights: t`Red Hat Insights`,
    archive: t`Remote Archive`,
  };

  const deleteJob = async () => {
    try {
      await getJobModel(job.type).destroy(job.id);
      history.push('/jobs');
    } catch (err) {
      setErrorMsg(err);
    }
  };

  const buildInstanceGroupLink = (item) => (
    <Link to={`/instance_groups/${item.id}`}>{item.name}</Link>
  );

  const buildContainerGroupLink = (item) => (
    <Link to={`/instance_groups/container_group/${item.id}`}>{item.name}</Link>
  );

  const renderInventoryDetail = () => {
    if (
      job.type !== 'project_update' &&
      job.type !== 'system_job' &&
      job.type !== 'workflow_job'
    ) {
      return inventory ? (
        <Detail
          dataCy="job-inventory"
          label={t`Inventory`}
          helpText={jobHelpText.inventory}
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
      ) : (
        <DeletedDetail label={t`Inventory`} helpText={jobHelpText.inventory} />
      );
    }
    if (job.type === 'workflow_job') {
      return inventory ? (
        <Detail
          dataCy="job-inventory"
          label={t`Inventory`}
          helpText={jobHelpText.inventory}
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
      ) : null;
    }
    return null;
  };

  const renderProjectDetail = () => {
    if (
      job.type !== 'ad_hoc_command' &&
      job.type !== 'inventory_update' &&
      job.type !== 'system_job' &&
      job.type !== 'workflow_job'
    ) {
      return project ? (
        <>
          <Detail
            dataCy="job-project"
            label={t`Project`}
            helpText={jobHelpText.project}
            value={<Link to={`/projects/${project.id}`}>{project.name}</Link>}
          />
          <Detail
            dataCy="job-project-status"
            label={t`Project Status`}
            value={
              projectUpdate ? (
                <Link to={`/jobs/project/${projectUpdate.id}`}>
                  <StatusLabel status={project.status} />
                </Link>
              ) : (
                <StatusLabel status={project.status} />
              )
            }
          />
        </>
      ) : (
        <DeletedDetail label={t`Project`} />
      );
    }
    return null;
  };

  return (
    <CardBody>
      <DetailList>
        <Detail dataCy="job-id" label={t`Job ID`} value={job.id} />
        <Detail
          dataCy="job-status"
          fullWidth={Boolean(job.job_explanation)}
          label={t`Status`}
          value={
            <StatusDetailValue>
              {job.status && <StatusLabel status={job.status} />}
              {job.job_explanation && job.job_explanation !== job.status
                ? job.job_explanation
                : null}
            </StatusDetailValue>
          }
        />
        <Detail
          dataCy="job-started-date"
          label={t`Started`}
          value={formatDateString(job.started)}
        />
        {job?.finished && (
          <Detail
            dataCy="job-finished-date"
            label={t`Finished`}
            value={formatDateString(job.finished)}
          />
        )}
        {jobTemplate && (
          <Detail
            dataCy="job-template"
            label={t`Job Template`}
            value={
              <Link to={`/templates/job_template/${jobTemplate.id}`}>
                {jobTemplate.name}
              </Link>
            }
          />
        )}
        {workflowJobTemplate && (
          <Detail
            dataCy="workflow-job-template"
            label={t`Workflow Job Template`}
            value={
              <Link
                to={`/templates/workflow_job_template/${workflowJobTemplate.id}`}
              >
                {workflowJobTemplate.name}
              </Link>
            }
          />
        )}
        {source_workflow_job && (
          <Detail
            dataCy="source-workflow-job"
            label={t`Source Workflow Job`}
            value={
              <Link to={`/jobs/workflow/${source_workflow_job.id}`}>
                {source_workflow_job.id} - {source_workflow_job.name}
              </Link>
            }
          />
        )}
        <Detail
          dataCy="job-type"
          label={t`Job Type`}
          helpText={jobHelpText.jobType}
          value={jobTypes[job.type]}
        />
        <Detail
          dataCy="source-control-type"
          label={t`Source Control Type`}
          value={scmTypes[job.scm_type]}
        />
        <LaunchedByDetail dataCy="job-launched-by" job={job} />
        {renderInventoryDetail()}
        {inventory_source && (
          <>
            <Detail
              dataCy="job-inventory-source"
              label={t`Inventory Source`}
              value={
                <Link
                  to={`/inventories/inventory/${inventory.id}/sources/${inventory_source.id}`}
                >
                  {inventory_source.name}
                </Link>
              }
            />
            {inventorySourceLabels.length > 0 && (
              <Detail
                dataCy="job-inventory-source-type"
                label={t`Source`}
                value={inventorySourceLabels.map(([string, label]) =>
                  string === job.source ? label : null
                )}
              />
            )}
          </>
        )}
        {inventory_source && inventory_source.source === 'scm' && (
          <Detail
            dataCy="job-inventory-source-project"
            label={t`Inventory Source Project`}
            value={
              <StatusDetailValue>
                {source_project.status && (
                  <StatusLabel status={source_project.status} />
                )}
                <Link to={`/projects/${source_project.id}`}>
                  {source_project.name}
                </Link>
              </StatusDetailValue>
            }
          />
        )}
        {renderProjectDetail()}
        {scmBranch && (
          <Detail
            dataCy="source-control-branch"
            label={t`Source Control Branch`}
            helpText={jobHelpText.sourceControlBranch}
            value={scmBranch}
          />
        )}
        <Detail
          dataCy="job-scm-revision"
          label={t`Revision`}
          value={job.scm_revision}
        />
        <Detail
          dataCy="job-playbook"
          label={t`Playbook`}
          helpText={jobHelpText.playbook}
          value={job.playbook}
        />
        <Detail
          dataCy="job-limit"
          label={t`Limit`}
          helpText={jobHelpText.limit}
          value={job.limit}
        />
        <Detail
          dataCy="job-verbosity"
          label={t`Verbosity`}
          helpText={jobHelpText.verbosity}
          value={VERBOSITY[job.verbosity]}
        />
        {job.type !== 'workflow_job' && !isJobRunning(job.status) && (
          <ExecutionEnvironmentDetail
            dataCy="job-execution-environment"
            executionEnvironment={executionEnvironment}
            helpText={jobHelpText.executionEnvironment}
            verifyMissingVirtualEnv={false}
          />
        )}
        <Detail
          dataCy="job-execution-node"
          label={t`Execution Node`}
          value={job.execution_node}
        />
        {instanceGroup && !instanceGroup?.is_container_group && (
          <Detail
            dataCy="job-instance-group"
            label={t`Instance Group`}
            helpText={jobHelpText.instanceGroups}
            value={buildInstanceGroupLink(instanceGroup)}
          />
        )}
        {instanceGroup && instanceGroup?.is_container_group && (
          <Detail
            dataCy="job-container-group"
            label={t`Container Group`}
            value={buildContainerGroupLink(instanceGroup)}
          />
        )}
        {typeof job.job_slice_number === 'number' &&
          typeof job.job_slice_count === 'number' && (
            <Detail
              dataCy="job-slice"
              label={t`Job Slice`}
              helpText={jobHelpText.jobSlicing}
              value={`${job.job_slice_number}/${job.job_slice_count}`}
            />
          )}
        {job.type === 'workflow_job' && job.is_sliced_job && (
          <Detail
            dataCy="job-slice-parent"
            label={t`Job Slice Parent`}
            value={t`True`}
          />
        )}
        {typeof job.forks === 'number' && (
          <Detail
            dataCy="forks"
            label={t`Forks`}
            value={`${job.forks}`}
            helpText={jobHelpText.forks}
          />
        )}

        {credential && (
          <Detail
            dataCy="job-machine-credential"
            label={t`Machine Credential`}
            value={
              <ChipGroup
                numChips={5}
                totalChips={1}
                ouiaId="job-machine-credential-chips"
              >
                <CredentialChip
                  key={credential.id}
                  credential={credential}
                  isReadOnly
                  ouiaId={`job-machine-credential-${credential.id}-chip`}
                />
              </ChipGroup>
            }
          />
        )}
        {credentials && credentials.length > 0 && (
          <Detail
            dataCy="job-credentials"
            fullWidth
            helpText={jobHelpText.credentials}
            label={t`Credentials`}
            value={
              <ChipGroup
                numChips={5}
                totalChips={credentials.length}
                ouiaId="job-credential-chips"
              >
                {credentials.map((c) => (
                  <CredentialChip
                    key={c.id}
                    credential={c}
                    isReadOnly
                    ouiaId={`job-credential-${c.id}-chip`}
                  />
                ))}
              </ChipGroup>
            }
          />
        )}
        {labels && labels.count > 0 && (
          <Detail
            dataCy="job-labels"
            fullWidth
            label={t`Labels`}
            helpText={jobHelpText.labels}
            value={
              <ChipGroup
                numChips={5}
                totalChips={labels.results.length}
                ouiaId="job-label-chips"
              >
                {labels.results.map((l) => (
                  <Chip key={l.id} isReadOnly ouiaId={`job-label-${l.id}-chip`}>
                    {l.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {job.job_tags && job.job_tags.length > 0 && (
          <Detail
            dataCy="job-tags"
            fullWidth
            label={t`Job Tags`}
            helpText={jobHelpText.jobTags}
            value={
              <ChipGroup
                numChips={5}
                totalChips={job.job_tags.split(',').length}
                ouiaId="job-tag-chips"
              >
                {job.job_tags.split(',').map((jobTag) => (
                  <Chip
                    key={jobTag}
                    isReadOnly
                    ouiaId={`job-tag-${jobTag}-chip`}
                  >
                    {jobTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {job.skip_tags && job.skip_tags.length > 0 && (
          <Detail
            dataCy="job-skip-tags"
            fullWidth
            label={t`Skip Tags`}
            helpText={jobHelpText.skipTags}
            value={
              <ChipGroup
                numChips={5}
                totalChips={job.skip_tags.split(',').length}
                ouiaId="job-skip-tag-chips"
              >
                {job.skip_tags.split(',').map((skipTag) => (
                  <Chip
                    key={skipTag}
                    isReadOnly
                    ouiaId={`job-skip-tag-${skipTag}-chip`}
                  >
                    {skipTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        <Detail
          dataCy="job-module-name"
          label={t`Module Name`}
          value={job.module_name}
          helpText={jobHelpText.module(job.module_name)}
        />
        <Detail
          dataCy="job-module-arguments"
          label={t`Module Arguments`}
          value={job.module_args}
        />
        <UserDateDetail
          label={t`Created`}
          date={job.created}
          user={created_by}
        />
        <UserDateDetail label={t`Last Modified`} date={job.modified} />
        {job.extra_vars && (
          <VariablesDetail
            css="margin: 20px 0"
            id="job-variables"
            readOnly
            value={job.extra_vars}
            rows={4}
            label={t`Variables`}
            name="extra_vars"
            dataCy="job-detail-extra-variables"
            helpText={jobHelpText.variables}
          />
        )}
        {job.artifacts && (
          <VariablesDetail
            css="margin: 20px 0"
            id="job-artifacts"
            readOnly
            value={JSON.stringify(job.artifacts)}
            rows={4}
            label={t`Artifacts`}
            name="artifacts"
            dataCy="job-detail-artifacts"
          />
        )}
      </DetailList>
      <CardActionsRow>
        {job.type !== 'system_job' &&
          job.summary_fields.user_capabilities.start &&
          (job.status === 'failed' && job.type === 'job' ? (
            <LaunchButton resource={job}>
              {({ handleRelaunch, isLaunching }) => (
                <ReLaunchDropDown
                  ouiaId="job-detail-relaunch-dropdown"
                  isPrimary
                  handleRelaunch={handleRelaunch}
                  isLaunching={isLaunching}
                />
              )}
            </LaunchButton>
          ) : (
            <LaunchButton resource={job} aria-label={t`Relaunch`}>
              {({ handleRelaunch, isLaunching }) => (
                <Button
                  ouiaId="job-detail-relaunch-button"
                  type="submit"
                  onClick={() => handleRelaunch()}
                  isDisabled={isLaunching}
                >
                  {t`Relaunch`}
                </Button>
              )}
            </LaunchButton>
          ))}
        {isJobRunning(job.status) &&
          (job.type === 'system_job'
            ? me.is_superuser
            : job?.summary_fields?.user_capabilities?.start) && (
            <JobCancelButton
              job={job}
              errorTitle={t`Job Cancel Error`}
              title={t`Cancel ${job.name}`}
              errorMessage={t`Failed to cancel ${job.name}`}
            />
          )}
        {!isJobRunning(job.status) &&
          job?.summary_fields?.user_capabilities?.delete && (
            <DeleteButton
              name={job.name}
              modalTitle={t`Delete Job`}
              onConfirm={deleteJob}
              ouiaId="job-detail-delete-button"
            >
              {t`Delete`}
            </DeleteButton>
          )}
      </CardActionsRow>
      {errorMsg && (
        <AlertModal
          isOpen={errorMsg}
          variant="error"
          onClose={() => setErrorMsg()}
          title={t`Job Delete Error`}
        >
          <ErrorDetail error={errorMsg} />
        </AlertModal>
      )}
    </CardBody>
  );
}
JobDetail.propTypes = {
  job: Job.isRequired,
};

export default JobDetail;
