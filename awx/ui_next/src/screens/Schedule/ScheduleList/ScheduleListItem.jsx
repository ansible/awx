import React from 'react';
import { bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  DataListItem,
  DataListItemRow,
  DataListItemCells as _DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';

import ActionButtonCell from '@components/ActionButtonCell';
import { DetailList, Detail } from '@components/DetailList';
import DataListCell from '@components/DataListCell';
import DataListCheck from '@components/DataListCheck';
import ListActionButton from '@components/ListActionButton';
import Switch from '@components/Switch';
import VerticalSeparator from '@components/VerticalSeparator';
import styled from 'styled-components';
import { Schedule } from '@types';
import { formatDateString } from '@util/dates';

const DataListItemCells = styled(_DataListItemCells)`
  ${DataListCell}:first-child {
    flex-grow: 2;
  }
`;

function ScheduleListItem({
  i18n,
  isSelected,
  onSelect,
  onToggleSchedule,
  schedule,
  toggleLoading,
}) {
  const labelId = `check-action-${schedule.id}`;

  const jobTypeLabels = {
    inventory_update: i18n._(t`Inventory Sync`),
    job: i18n._(t`Playbook Run`),
    project_update: i18n._(t`SCM Update`),
    system_job: i18n._(t`Management Job`),
    workflow_job: i18n._(t`Workflow Job`),
  };

  let scheduleBaseUrl;

  switch (schedule.summary_fields.unified_job_template.unified_job_type) {
    case 'inventory_update':
      scheduleBaseUrl = `/inventories/${schedule.summary_fields.inventory.id}/sources/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
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
    <DataListItem
      key={schedule.id}
      aria-labelledby={labelId}
      id={`${schedule.id}`}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-schedule-${schedule.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />
        <DataListItemCells
          dataListCells={[
            <DataListCell key="name">
              <VerticalSeparator />
              <Link to={`${scheduleBaseUrl}/details`}>
                <b>{schedule.name}</b>
              </Link>
            </DataListCell>,
            <DataListCell key="type">
              {
                jobTypeLabels[
                  schedule.summary_fields.unified_job_template.unified_job_type
                ]
              }
            </DataListCell>,
            <DataListCell key="next_run">
              {schedule.next_run && (
                <DetailList stacked>
                  <Detail
                    label={i18n._(t`Next Run`)}
                    value={formatDateString(schedule.next_run)}
                  />
                </DetailList>
              )}
            </DataListCell>,
            <ActionButtonCell lastcolumn="true" key="action">
              <Tooltip
                content={
                  schedule.enabled
                    ? i18n._(t`Schedule is active`)
                    : i18n._(t`Schedule is inactive`)
                }
                position="top"
              >
                <Switch
                  id={`schedule-${schedule.id}-toggle`}
                  label={i18n._(t`On`)}
                  labelOff={i18n._(t`Off`)}
                  isChecked={schedule.enabled}
                  isDisabled={
                    toggleLoading ||
                    !schedule.summary_fields.user_capabilities.edit
                  }
                  onChange={() => onToggleSchedule(schedule)}
                  aria-label={i18n._(t`Toggle schedule`)}
                />
              </Tooltip>
              {schedule.summary_fields.user_capabilities.edit && (
                <Tooltip content={i18n._(t`Edit Schedule`)} position="top">
                  <ListActionButton
                    variant="plain"
                    component={Link}
                    to={`${scheduleBaseUrl}/edit`}
                  >
                    <PencilAltIcon />
                  </ListActionButton>
                </Tooltip>
              )}
            </ActionButtonCell>,
          ]}
        />
      </DataListItemRow>
    </DataListItem>
  );
}

ScheduleListItem.propTypes = {
  isSelected: bool.isRequired,
  onToggleSchedule: func.isRequired,
  onSelect: func.isRequired,
  schedule: Schedule.isRequired,
};

export default withI18n()(ScheduleListItem);
