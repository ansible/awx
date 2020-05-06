import React from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { shape, func } from 'prop-types';
import {
  DownloadIcon,
  RocketIcon,
  TrashAltIcon,
} from '@patternfly/react-icons';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';
import DeleteButton from '../../../../components/DeleteButton';
import LaunchButton from '../../../../components/LaunchButton';

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
  ${props =>
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

const toHHMMSS = elapsed => {
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

const OutputToolbar = ({ i18n, job, onDelete }) => {
  const hideCounts = OUTPUT_NO_COUNT_JOB_TYPES.includes(job.type);

  const playCount = job?.playbook_counts?.play_count;
  const taskCount = job?.playbook_counts?.task_count;
  const darkCount = job?.host_status_counts?.dark;
  const failureCount = job?.host_status_counts?.failures;
  const totalHostCount = Object.keys(job?.host_status_counts || {}).reduce(
    (sum, key) => sum + job?.host_status_counts[key],
    0
  );

  return (
    <Wrapper>
      {!hideCounts && (
        <>
          {playCount > 0 && (
            <BadgeGroup aria-label={i18n._(t`Play Count`)}>
              <div>{i18n._(t`Plays`)}</div>
              <Badge isRead>{playCount}</Badge>
            </BadgeGroup>
          )}
          {taskCount > 0 && (
            <BadgeGroup aria-label={i18n._(t`Task Count`)}>
              <div>{i18n._(t`Tasks`)}</div>
              <Badge isRead>{taskCount}</Badge>
            </BadgeGroup>
          )}
          {totalHostCount > 0 && (
            <BadgeGroup aria-label={i18n._(t`Host Count`)}>
              <div>{i18n._(t`Hosts`)}</div>
              <Badge isRead>{totalHostCount}</Badge>
            </BadgeGroup>
          )}
          {darkCount > 0 && (
            <BadgeGroup aria-label={i18n._(t`Unreachable Host Count`)}>
              <div>{i18n._(t`Unreachable`)}</div>
              <Tooltip content={i18n._(t`Unreachable Hosts`)}>
                <Badge color="#470000" isRead>
                  {darkCount}
                </Badge>
              </Tooltip>
            </BadgeGroup>
          )}
          {failureCount > 0 && (
            <BadgeGroup aria-label={i18n._(t`Failed Host Count`)}>
              <div>{i18n._(t`Failed`)}</div>
              <Tooltip content={i18n._(t`Failed Hosts`)}>
                <Badge color="#C9190B" isRead>
                  {failureCount}
                </Badge>
              </Tooltip>
            </BadgeGroup>
          )}
        </>
      )}

      <BadgeGroup aria-label={i18n._(t`Elapsed Time`)}>
        <div>{i18n._(t`Elapsed`)}</div>
        <Tooltip content={i18n._(t`Elapsed time that the job ran`)}>
          <Badge isRead>{toHHMMSS(job.elapsed)}</Badge>
        </Tooltip>
      </BadgeGroup>

      {job.type !== 'system_job' &&
        job.summary_fields.user_capabilities?.start && (
          <Tooltip content={i18n._(t`Relaunch Job`)}>
            <LaunchButton resource={job} aria-label={i18n._(t`Relaunch`)}>
              {({ handleRelaunch }) => (
                <Button
                  variant="plain"
                  onClick={handleRelaunch}
                  aria-label={i18n._(t`Relaunch`)}
                >
                  <RocketIcon />
                </Button>
              )}
            </LaunchButton>
          </Tooltip>
        )}

      {job.related?.stdout && (
        <Tooltip content={i18n._(t`Download Output`)}>
          <a href={`${job.related.stdout}?format=txt_download`}>
            <Button variant="plain" aria-label={i18n._(t`Download Output`)}>
              <DownloadIcon />
            </Button>
          </a>
        </Tooltip>
      )}

      {job.summary_fields.user_capabilities.delete && (
        <Tooltip content={i18n._(t`Delete Job`)}>
          <DeleteButton
            name={job.name}
            modalTitle={i18n._(t`Delete Job`)}
            onConfirm={onDelete}
            variant="plain"
          >
            <TrashAltIcon />
          </DeleteButton>
        </Tooltip>
      )}
    </Wrapper>
  );
};

OutputToolbar.propTypes = {
  job: shape({}).isRequired,
  onDelete: func.isRequired,
};

export default withI18n()(OutputToolbar);
