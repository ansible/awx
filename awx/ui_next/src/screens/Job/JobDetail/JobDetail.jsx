import 'styled-components/macro';
import React, { useCallback, useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Chip } from '@patternfly/react-core';
import styled from 'styled-components';

import AlertModal from '../../../components/AlertModal';
import {
  DetailList,
  Detail,
  UserDateDetail,
  LaunchedByDetail,
} from '../../../components/DetailList';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ChipGroup from '../../../components/ChipGroup';
import CredentialChip from '../../../components/CredentialChip';
import { VariablesInput as _VariablesInput } from '../../../components/CodeEditor';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import {
  LaunchButton,
  ReLaunchDropDown,
} from '../../../components/LaunchButton';
import StatusIcon from '../../../components/StatusIcon';
import ExecutionEnvironmentDetail from '../../../components/ExecutionEnvironmentDetail';
import { getJobModel, isJobRunning } from '../../../util/jobs';
import { toTitleCase } from '../../../util/strings';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { formatDateString } from '../../../util/dates';
import { Job } from '../../../types';

const VariablesInput = styled(_VariablesInput)`
  .pf-c-form__label {
    --pf-c-form__label--FontWeight: var(--pf-global--FontWeight--bold);
  }
`;

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

function JobDetail({ job, i18n }) {
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
    source_workflow_job,
    execution_environment: executionEnvironment,
  } = job.summary_fields;
  const [errorMsg, setErrorMsg] = useState();
  const history = useHistory();

  const [showCancelModal, setShowCancelModal] = useState(false);

  const {
    error: cancelError,
    isLoading: isCancelling,
    request: cancelJob,
  } = useRequest(
    useCallback(async () => {
      await getJobModel(job.type).cancel(job.id, job.type);
    }, [job.id, job.type]),
    {}
  );

  const {
    error: dismissableCancelError,
    dismissError: dismissCancelError,
  } = useDismissableError(cancelError);

  const jobTypes = {
    project_update: i18n._(t`Source Control Update`),
    inventory_update: i18n._(t`Inventory Sync`),
    job:
      job.job_type === 'check'
        ? i18n._(t`Playbook Check`)
        : i18n._(t`Playbook Run`),
    ad_hoc_command: i18n._(t`Command`),
    management_job: i18n._(t`Management Job`),
    workflow_job: i18n._(t`Workflow Job`),
  };

  const deleteJob = async () => {
    try {
      await getJobModel(job.type).destroy(job.id);
      history.push('/jobs');
    } catch (err) {
      setErrorMsg(err);
    }
  };

  const buildInstanceGroupLink = item => {
    return <Link to={`/instance_groups/${item.id}`}>{item.name}</Link>;
  };

  const buildContainerGroupLink = item => {
    return (
      <Link to={`/instance_groups/container_group/${item.id}`}>
        {item.name}
      </Link>
    );
  };

  return (
    <CardBody>
      <DetailList>
        <Detail
          fullWidth={Boolean(job.job_explanation)}
          label={i18n._(t`Status`)}
          value={
            <StatusDetailValue>
              {job.status && <StatusIcon status={job.status} />}
              {job.job_explanation
                ? job.job_explanation
                : toTitleCase(job.status)}
            </StatusDetailValue>
          }
        />
        <Detail
          label={i18n._(t`Started`)}
          value={formatDateString(job.started)}
        />
        <Detail
          label={i18n._(t`Finished`)}
          value={formatDateString(job.finished)}
        />
        {jobTemplate && (
          <Detail
            label={i18n._(t`Job Template`)}
            value={
              <Link to={`/templates/job_template/${jobTemplate.id}`}>
                {jobTemplate.name}
              </Link>
            }
          />
        )}
        {workflowJobTemplate && (
          <Detail
            label={i18n._(t`Workflow Job Template`)}
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
            label={i18n._(t`Source Workflow Job`)}
            value={
              <Link to={`/jobs/workflow/${source_workflow_job.id}`}>
                {source_workflow_job.id} - {source_workflow_job.name}
              </Link>
            }
          />
        )}
        <Detail label={i18n._(t`Job Type`)} value={jobTypes[job.type]} />
        <LaunchedByDetail job={job} i18n={i18n} />
        {inventory && (
          <Detail
            label={i18n._(t`Inventory`)}
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
        {inventory_source && (
          <Detail
            label={i18n._(t`Inventory Source`)}
            value={
              <Link
                to={`/inventories/inventory/${inventory.id}/sources/${inventory_source.id}`}
              >
                {inventory_source.name}
              </Link>
            }
          />
        )}
        {inventory_source && inventory_source.source === 'scm' && (
          <Detail
            label={i18n._(t`Project`)}
            value={
              <StatusDetailValue>
                {source_project.status && (
                  <StatusIcon status={source_project.status} />
                )}
                <Link to={`/projects/${source_project.id}`}>
                  {source_project.name}
                </Link>
              </StatusDetailValue>
            }
          />
        )}
        {project && (
          <Detail
            label={i18n._(t`Project`)}
            value={
              <StatusDetailValue>
                {project.status && <StatusIcon status={project.status} />}
                <Link to={`/projects/${project.id}`}>{project.name}</Link>
              </StatusDetailValue>
            }
          />
        )}
        <Detail label={i18n._(t`Revision`)} value={job.scm_revision} />
        <Detail label={i18n._(t`Playbook`)} value={job.playbook} />
        <Detail label={i18n._(t`Limit`)} value={job.limit} />
        <Detail label={i18n._(t`Verbosity`)} value={VERBOSITY[job.verbosity]} />
        <ExecutionEnvironmentDetail
          virtualEnvironment={job.custom_virtualenv}
          executionEnvironment={executionEnvironment}
        />
        <Detail label={i18n._(t`Execution Node`)} value={job.execution_node} />
        {instanceGroup && !instanceGroup?.is_container_group && (
          <Detail
            label={i18n._(t`Instance Group`)}
            value={buildInstanceGroupLink(instanceGroup)}
          />
        )}
        {instanceGroup && instanceGroup?.is_container_group && (
          <Detail
            label={i18n._(t`Container Group`)}
            value={buildContainerGroupLink(instanceGroup)}
          />
        )}
        {typeof job.job_slice_number === 'number' &&
          typeof job.job_slice_count === 'number' && (
            <Detail
              label={i18n._(t`Job Slice`)}
              value={`${job.job_slice_number}/${job.job_slice_count}`}
            />
          )}
        {credential && (
          <Detail
            label={i18n._(t`Machine Credential`)}
            value={
              <ChipGroup numChips={5} totalChips={1}>
                <CredentialChip
                  key={credential.id}
                  credential={credential}
                  isReadOnly
                />
              </ChipGroup>
            }
          />
        )}
        {credentials && credentials.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credentials`)}
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
            label={i18n._(t`Labels`)}
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
        {job.job_tags && job.job_tags.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Job Tags`)}
            value={
              <ChipGroup
                numChips={5}
                totalChips={job.job_tags.split(',').length}
              >
                {job.job_tags.split(',').map(jobTag => (
                  <Chip key={jobTag} isReadOnly>
                    {jobTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {job.skip_tags && job.skip_tags.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Skip Tags`)}
            value={
              <ChipGroup
                numChips={5}
                totalChips={job.skip_tags.split(',').length}
              >
                {job.skip_tags.split(',').map(skipTag => (
                  <Chip key={skipTag} isReadOnly>
                    {skipTag}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={job.created}
          user={created_by}
        />
        <UserDateDetail label={i18n._(t`Last Modified`)} date={job.modified} />
      </DetailList>
      {job.extra_vars && (
        <VariablesInput
          css="margin: 20px 0"
          id="job-variables"
          readOnly
          value={job.extra_vars}
          rows={4}
          label={i18n._(t`Variables`)}
        />
      )}
      {job.artifacts && (
        <VariablesInput
          css="margin: 20px 0"
          id="job-artifacts"
          readOnly
          value={JSON.stringify(job.artifacts)}
          rows={4}
          label={i18n._(t`Artifacts`)}
        />
      )}
      <CardActionsRow>
        {job.type !== 'system_job' &&
          job.summary_fields.user_capabilities.start &&
          (job.status === 'failed' && job.type === 'job' ? (
            <LaunchButton resource={job}>
              {({ handleRelaunch, isSending }) => (
                <ReLaunchDropDown
                  ouiaId="job-detail-relaunch-dropdown"
                  isPrimary
                  handleRelaunch={handleRelaunch}
                  isSending={isSending}
                />
              )}
            </LaunchButton>
          ) : (
            <LaunchButton resource={job} aria-label={i18n._(t`Relaunch`)}>
              {({ handleRelaunch, isSending }) => (
                <Button
                  ouiaId="job-detail-relaunch-button"
                  type="submit"
                  onClick={handleRelaunch}
                  isDisabled={isSending}
                >
                  {i18n._(t`Relaunch`)}
                </Button>
              )}
            </LaunchButton>
          ))}
        {isJobRunning(job.status) &&
          job?.summary_fields?.user_capabilities?.start && (
            <Button
              variant="secondary"
              aria-label={i18n._(t`Cancel`)}
              isDisabled={isCancelling}
              onClick={() => setShowCancelModal(true)}
              ouiaId="job-detail-cancel-button"
            >
              {i18n._(t`Cancel`)}
            </Button>
          )}
        {!isJobRunning(job.status) &&
          job?.summary_fields?.user_capabilities?.delete && (
            <DeleteButton
              name={job.name}
              modalTitle={i18n._(t`Delete Job`)}
              onConfirm={deleteJob}
              ouiaId="job-detail-delete-button"
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {showCancelModal && isJobRunning(job.status) && (
        <AlertModal
          isOpen={showCancelModal}
          variant="danger"
          onClose={() => setShowCancelModal(false)}
          title={i18n._(t`Cancel Job`)}
          label={i18n._(t`Cancel Job`)}
          actions={[
            <Button
              id="cancel-job-confirm-button"
              key="delete"
              variant="danger"
              isDisabled={isCancelling}
              aria-label={i18n._(t`Cancel job`)}
              onClick={cancelJob}
            >
              {i18n._(t`Cancel job`)}
            </Button>,
            <Button
              id="cancel-job-return-button"
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`Return`)}
              onClick={() => setShowCancelModal(false)}
            >
              {i18n._(t`Return`)}
            </Button>,
          ]}
        >
          {i18n._(
            t`Are you sure you want to submit the request to cancel this job?`
          )}
        </AlertModal>
      )}
      {dismissableCancelError && (
        <AlertModal
          isOpen={dismissableCancelError}
          variant="danger"
          onClose={dismissCancelError}
          title={i18n._(t`Job Cancel Error`)}
          label={i18n._(t`Job Cancel Error`)}
        >
          <ErrorDetail error={dismissableCancelError} />
        </AlertModal>
      )}
      {errorMsg && (
        <AlertModal
          isOpen={errorMsg}
          variant="error"
          onClose={() => setErrorMsg()}
          title={i18n._(t`Job Delete Error`)}
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

export default withI18n()(JobDetail);
