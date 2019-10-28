import React, { useState } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';

import AlertModal from '@components/AlertModal';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip, CredentialChip } from '@components/Chip';
import { VariablesInput as _VariablesInput } from '@components/CodeMirrorInput';
import ErrorDetail from '@components/ErrorDetail';
import LaunchButton from '@components/LaunchButton';
import { StatusIcon } from '@components/Sparkline';
import { toTitleCase } from '@util/strings';
import { formatDateString } from '@util/dates';
import { Job } from '@types';
import {
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  WorkflowJobsAPI,
  InventoriesAPI,
  AdHocCommandsAPI,
} from '@api';
import { JOB_TYPE_URL_SEGMENTS } from '../../../constants';

const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;

const VariablesInput = styled(_VariablesInput)`
  .pf-c-form__label {
    --pf-c-form__label--FontWeight: var(--pf-global--FontWeight--bold);
  }
`;

const StatusDetailValue = styled.div`
  align-items: center;
  display: inline-flex;
  .at-c-statusIcon {
    margin-right: 10px;
  }
`;

const VERBOSITY = {
  0: '0 (Normal)',
  1: '1 (Verbose)',
  2: '2 (More Verbose)',
  3: '3 (Debug)',
  4: '4 (Connection Debug)',
};

const getLaunchedByDetails = ({ summary_fields = {}, related = {} }) => {
  const {
    created_by: createdBy,
    job_template: jobTemplate,
    schedule,
  } = summary_fields;
  const { schedule: relatedSchedule } = related;

  if (!createdBy && !schedule) {
    return null;
  }

  let link;
  let value;

  if (createdBy) {
    link = `/users/${createdBy.id}`;
    value = createdBy.username;
  } else if (relatedSchedule && jobTemplate) {
    link = `/templates/job_template/${jobTemplate.id}/schedules/${schedule.id}`;
    value = schedule.name;
  } else {
    link = null;
    value = schedule.name;
  }

  return { link, value };
};

function JobDetail({ job, i18n, history }) {
  const {
    credentials,
    instance_group: instanceGroup,
    inventory,
    job_template: jobTemplate,
    labels,
    project,
  } = job.summary_fields;
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState();

  const { value: launchedByValue, link: launchedByLink } =
    getLaunchedByDetails(job) || {};

  const deleteJob = async () => {
    try {
      switch (job.type) {
        case 'project_update':
          await ProjectUpdatesAPI.destroy(job.id);
          break;
        case 'system_job':
          await SystemJobsAPI.destroy(job.id);
          break;
        case 'workflow_job':
          await WorkflowJobsAPI.destroy(job.id);
          break;
        case 'ad_hoc_command':
          await AdHocCommandsAPI.destroy(job.id);
          break;
        case 'inventory_update':
          await InventoriesAPI.destroy(job.id);
          break;
        default:
          await JobsAPI.destroy(job.id);
      }
      history.push('/jobs');
    } catch (err) {
      setErrorMsg(err);
      setIsDeleteModalOpen(false);
    }
  };

  return (
    <CardBody>
      <DetailList>
        {/* TODO: hookup status to websockets */}
        <Detail
          label={i18n._(t`Status`)}
          value={
            <StatusDetailValue>
              {job.status && <StatusIcon status={job.status} />}
              {toTitleCase(job.status)}
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
            label={i18n._(t`Template`)}
            value={
              <Link to={`/templates/job_template/${jobTemplate.id}`}>
                {jobTemplate.name}
              </Link>
            }
          />
        )}
        <Detail label={i18n._(t`Job Type`)} value={toTitleCase(job.job_type)} />
        <Detail
          label={i18n._(t`Launched By`)}
          value={
            launchedByLink ? (
              <Link to={`${launchedByLink}`}>{launchedByValue}</Link>
            ) : (
              launchedByValue
            )
          }
        />
        {inventory && (
          <Detail
            label={i18n._(t`Inventory`)}
            value={
              <Link to={`/inventory/${inventory.id}`}>{inventory.name}</Link>
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
        <Detail label={i18n._(t`Environment`)} value={job.custom_virtualenv} />
        <Detail label={i18n._(t`Execution Node`)} value={job.execution_node} />
        {instanceGroup && (
          <Detail
            label={i18n._(t`Instance Group`)}
            value={
              <Link to={`/instance_groups/${instanceGroup.id}`}>
                {instanceGroup.name}
              </Link>
            }
          />
        )}
        {typeof job.job_slice_number === 'number' &&
          typeof job.job_slice_count === 'number' && (
            <Detail
              label={i18n._(t`Job Slice`)}
              value={`${job.job_slice_number}/${job.job_slice_count}`}
            />
          )}
        {credentials && credentials.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credentials`)}
            value={
              <ChipGroup showOverflowAfter={5}>
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
              <ChipGroup showOverflowAfter={5}>
                {labels.results.map(l => (
                  <Chip key={l.id} isReadOnly>
                    {l.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
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
      <ActionButtonWrapper>
        {job.type !== 'system_job' &&
          job.summary_fields.user_capabilities.start && (
            <LaunchButton resource={job} aria-label={i18n._(t`Relaunch`)}>
              {({ handleRelaunch }) => (
                <Button type="submit" onClick={handleRelaunch}>
                  {i18n._(t`Relaunch`)}
                </Button>
              )}
            </LaunchButton>
          )}
        {job.summary_fields.user_capabilities.delete && (
          <Button
            variant="danger"
            aria-label={i18n._(t`Delete`)}
            onClick={() => setIsDeleteModalOpen(true)}
          >
            {i18n._(t`Delete`)}
          </Button>
        )}
      </ActionButtonWrapper>
      {isDeleteModalOpen && (
        <AlertModal
          isOpen={isDeleteModalOpen}
          title={i18n._(t`Delete Job`)}
          variant="danger"
          onClose={() => setIsDeleteModalOpen(false)}
        >
          {i18n._(t`Are you sure you want to delete:`)}
          <br />
          <strong>{job.name}</strong>
          <ActionButtonWrapper>
            <Button
              variant="secondary"
              aria-label={i18n._(t`Close`)}
              component={Link}
              to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}
            >
              {i18n._(t`Cancel`)}
            </Button>

            <Button
              variant="danger"
              aria-label={i18n._(t`Delete`)}
              onClick={deleteJob}
            >
              {i18n._(t`Delete`)}
            </Button>
          </ActionButtonWrapper>
        </AlertModal>
      )}
      {errorMsg && (
        <AlertModal
          isOpen={errorMsg}
          variant="danger"
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

export default withI18n()(withRouter(JobDetail));
