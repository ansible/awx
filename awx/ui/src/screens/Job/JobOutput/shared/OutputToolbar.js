import React from 'react';
import styled from 'styled-components';

import { t } from '@lingui/macro';
import { bool, shape, func } from 'prop-types';
import {
  DownloadIcon,
  RocketIcon,
  TrashAltIcon,
} from '@patternfly/react-icons';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';
import DeleteButton from 'components/DeleteButton';
import { LaunchButton, ReLaunchDropDown } from 'components/LaunchButton';
import { useConfig } from 'contexts/Config';

import JobCancelButton from 'components/JobCancelButton';

const BadgeGroup = styled.div`
  margin-left: 20px;
  height: 18px;
  display: inline-flex;
`;

const Badge = styled(PFBadge)`
  align-items: center;
  display: flex;
  justify-content: center;
  margin-left: 10px;
  ${(props) =>
    props.color
      ? `
  background-color: ${props.color}
  color: white;
  `
      : null}
`;

const Wrapper = styled.div`
  align-items: center;
  display: flex;
  flex-flow: row wrap;
  font-size: 14px;
`;

const toHHMMSS = (elapsed) => {
  const sec_num = parseInt(elapsed, 10);
  const hours = Math.floor(sec_num / 3600);
  const minutes = Math.floor(sec_num / 60) % 60;
  const seconds = sec_num % 60;

  const stampHours = hours < 10 ? `0${hours}` : hours;
  const stampMinutes = minutes < 10 ? `0${minutes}` : minutes;
  const stampSeconds = seconds < 10 ? `0${seconds}` : seconds;

  return `${stampHours}:${stampMinutes}:${stampSeconds}`;
};

const OUTPUT_NO_COUNT_JOB_TYPES = [
  'ad_hoc_command',
  'system_job',
  'inventory_update',
];

const OutputToolbar = ({ job, onDelete, isDeleteDisabled, jobStatus }) => {
  const hideCounts = OUTPUT_NO_COUNT_JOB_TYPES.includes(job.type);

  const playCount = job?.playbook_counts?.play_count;
  const taskCount = job?.playbook_counts?.task_count;
  const darkCount = job?.host_status_counts?.dark;
  const failureCount = job?.host_status_counts?.failures;
  const totalHostCount = job?.host_status_counts
    ? Object.keys(job.host_status_counts || {}).reduce(
        (sum, key) => sum + job.host_status_counts[key],
        0
      )
    : 0;
  const { me } = useConfig();

  return (
    <Wrapper>
      {!hideCounts && (
        <>
          {playCount > 0 && (
            <BadgeGroup aria-label={t`Play Count`}>
              <div>{t`Plays`}</div>
              <Badge isRead>{playCount}</Badge>
            </BadgeGroup>
          )}
          {taskCount > 0 && (
            <BadgeGroup aria-label={t`Task Count`}>
              <div>{t`Tasks`}</div>
              <Badge isRead>{taskCount}</Badge>
            </BadgeGroup>
          )}
          {totalHostCount > 0 && (
            <BadgeGroup aria-label={t`Host Count`}>
              <div>{t`Hosts`}</div>
              <Badge isRead>{totalHostCount}</Badge>
            </BadgeGroup>
          )}
          {darkCount > 0 && (
            <BadgeGroup aria-label={t`Unreachable Host Count`}>
              <div>{t`Unreachable`}</div>
              <Tooltip content={t`Unreachable Hosts`}>
                <Badge color="#470000" isRead>
                  {darkCount}
                </Badge>
              </Tooltip>
            </BadgeGroup>
          )}
          {failureCount > 0 && (
            <BadgeGroup aria-label={t`Failed Host Count`}>
              <div>{t`Failed`}</div>
              <Tooltip content={t`Failed Hosts`}>
                <Badge color="#C9190B" isRead>
                  {failureCount}
                </Badge>
              </Tooltip>
            </BadgeGroup>
          )}
        </>
      )}

      <BadgeGroup aria-label={t`Elapsed Time`}>
        <div>{t`Elapsed`}</div>
        <Tooltip content={t`Elapsed time that the job ran`}>
          <Badge isRead>{toHHMMSS(job.elapsed)}</Badge>
        </Tooltip>
      </BadgeGroup>
      {['pending', 'waiting', 'running'].includes(jobStatus) &&
        (job.type === 'system_job'
          ? me.is_superuser
          : job?.summary_fields?.user_capabilities?.start) && (
          <JobCancelButton
            job={job}
            errorTitle={t`Job Cancel Error`}
            title={t`Cancel ${job.name}`}
            errorMessage={t`Failed to cancel ${job.name}`}
            showIconButton
          />
        )}
      {job.summary_fields.user_capabilities?.start && (
        <Tooltip
          content={
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
                  ouiaId="job-output-relaunch-dropdown"
                  isLaunching={isLaunching}
                />
              )}
            </LaunchButton>
          ) : (
            <LaunchButton resource={job}>
              {({ handleRelaunch, isLaunching }) => (
                <Button
                  ouiaId="job-output-relaunch-button"
                  variant="plain"
                  onClick={() => handleRelaunch()}
                  aria-label={t`Relaunch`}
                  isDisabled={isLaunching}
                >
                  <RocketIcon />
                </Button>
              )}
            </LaunchButton>
          )}
        </Tooltip>
      )}

      {job.related?.stdout && (
        <Tooltip content={t`Download Output`}>
          <a href={`${job.related.stdout}?format=txt_download`}>
            <Button
              ouiaId="job-output-download-button"
              variant="plain"
              aria-label={t`Download Output`}
            >
              <DownloadIcon />
            </Button>
          </a>
        </Tooltip>
      )}
      {job.summary_fields.user_capabilities.delete &&
        ['new', 'successful', 'failed', 'error', 'canceled'].includes(
          jobStatus
        ) && (
          <Tooltip content={t`Delete Job`}>
            <DeleteButton
              ouiaId="job-output-delete-button"
              name={job.name}
              modalTitle={t`Delete Job`}
              onConfirm={onDelete}
              variant="plain"
              isDisabled={isDeleteDisabled}
            >
              <TrashAltIcon />
            </DeleteButton>
          </Tooltip>
        )}
    </Wrapper>
  );
};

OutputToolbar.propTypes = {
  isDeleteDisabled: bool,
  job: shape({}).isRequired,
  onDelete: func.isRequired,
};

OutputToolbar.defaultProps = {
  isDeleteDisabled: false,
};

export default OutputToolbar;
