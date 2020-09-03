import 'styled-components/macro';
import React from 'react';
import { bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import DataListCell from '../../DataListCell';
import { DetailList, Detail } from '../../DetailList';
import { ScheduleToggle } from '..';
import { Schedule } from '../../../types';
import { formatDateString } from '../../../util/dates';

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 92px 40px;
`;

function ScheduleListItem({ i18n, isSelected, onSelect, schedule }) {
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
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
          key="actions"
        >
          <ScheduleToggle schedule={schedule} />
          {schedule.summary_fields.user_capabilities.edit ? (
            <Tooltip content={i18n._(t`Edit Schedule`)} position="top">
              <Button
                aria-label={i18n._(t`Edit Schedule`)}
                css="grid-column: 2"
                variant="plain"
                component={Link}
                to={`${scheduleBaseUrl}/edit`}
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          ) : (
            ''
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}

ScheduleListItem.propTypes = {
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
  schedule: Schedule.isRequired,
};

export default withI18n()(ScheduleListItem);
