import 'styled-components/macro';
import React from 'react';
import { bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';
import { DetailList, Detail } from '../../DetailList';
import { ActionsTd, ActionItem } from '../../PaginatedTable';
import { ScheduleToggle } from '..';
import { Schedule } from '../../../types';
import { formatDateString } from '../../../util/dates';

function ScheduleListItem({ i18n, isSelected, onSelect, schedule, rowIndex }) {
  const labelId = `check-action-${schedule.id}`;

  const jobTypeLabels = {
    inventory_update: i18n._(t`Inventory Sync`),
    job: i18n._(t`Playbook Run`),
    project_update: i18n._(t`Source Control Update`),
    system_job: i18n._(t`Management Job`),
    workflow_job: i18n._(t`Workflow Job`),
  };

  let scheduleBaseUrl;

  switch (schedule.summary_fields.unified_job_template.unified_job_type) {
    case 'inventory_update':
      scheduleBaseUrl = `/inventories/inventory/${schedule.summary_fields.inventory.id}/sources/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      break;
    case 'job':
      scheduleBaseUrl = `/templates/job_template/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      break;
    case 'project_update':
      scheduleBaseUrl = `/projects/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      break;
    case 'system_job':
      scheduleBaseUrl = `/management_jobs/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      break;
    case 'workflow_job':
      scheduleBaseUrl = `/templates/workflow_job_template/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      break;
    default:
      break;
  }

  return (
    <Tr id={`schedule-row-${schedule.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
          disable: false,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${scheduleBaseUrl}/details`}>
          <b>{schedule.name}</b>
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Type`)}>
        {
          jobTypeLabels[
            schedule.summary_fields.unified_job_template.unified_job_type
          ]
        }
      </Td>
      <Td dataLabel={i18n._(t`Next Run`)}>
        {schedule.next_run && (
          <DetailList stacked>
            <Detail
              label={i18n._(t`Next Run`)}
              value={formatDateString(schedule.next_run)}
            />
          </DetailList>
        )}
      </Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)} gridColumns="auto 40px">
        <ScheduleToggle schedule={schedule} />
        <ActionItem
          visible={schedule.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit Schedule`)}
        >
          <Button
            aria-label={i18n._(t`Edit Schedule`)}
            css="grid-column: 2"
            variant="plain"
            component={Link}
            to={`${scheduleBaseUrl}/edit`}
          >
            <PencilAltIcon />
          </Button>
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}

ScheduleListItem.propTypes = {
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
  schedule: Schedule.isRequired,
};

export default withI18n()(ScheduleListItem);
