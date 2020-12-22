import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { RocketIcon } from '@patternfly/react-icons';
import { ActionsTd, ActionItem } from '../PaginatedTable';
import LaunchButton from '../LaunchButton';
import StatusLabel from '../StatusLabel';
import { formatDateString } from '../../util/dates';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

function JobListItem({
  i18n,
  job,
  rowIndex,
  isSelected,
  onSelect,
  showTypeColumn = false,
}) {
  const labelId = `check-action-${job.id}`;

  const jobTypes = {
    project_update: i18n._(t`Source Control Update`),
    inventory_update: i18n._(t`Inventory Sync`),
    job: i18n._(t`Playbook Run`),
    ad_hoc_command: i18n._(t`Command`),
    management_job: i18n._(t`Management Job`),
    workflow_job: i18n._(t`Workflow Job`),
  };

  return (
    <Tr id={`job-row-${job.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
          disable: false,
        }}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <span>
          <Link to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}>
            <b>
              {job.id} &mdash; {job.name}
            </b>
          </Link>
        </span>
      </Td>
      <Td dataLabel={i18n._(t`Status`)}>
        {job.status && <StatusLabel status={job.status} />}
      </Td>
      {showTypeColumn && (
        <Td dataLabel={i18n._(t`Type`)}>{jobTypes[job.type]}</Td>
      )}
      <Td dataLabel={i18n._(t`Start Time`)}>{formatDateString(job.started)}</Td>
      <Td dataLabel={i18n._(t`Finish Time`)}>
        {job.finished ? formatDateString(job.finished) : ''}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={
            job.type !== 'system_job' &&
            job.summary_fields?.user_capabilities?.start
          }
          tooltip={i18n._(t`Relaunch Job`)}
        >
          <LaunchButton resource={job}>
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
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

export { JobListItem as _JobListItem };
export default withI18n()(JobListItem);
