import 'styled-components/macro';
import React from 'react';
import { bool, func } from 'prop-types';

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import { Button, Tooltip } from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import {
  PencilAltIcon,
  ExclamationTriangleIcon as PFExclamationTriangleIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import { Schedule } from 'types';
import { formatDateString } from 'util/dates';
import { DetailList, Detail } from '../../DetailList';
import { ActionsTd, ActionItem, TdBreakWord } from '../../PaginatedTable';
import { ScheduleToggle } from '..';

const ExclamationTriangleIcon = styled(PFExclamationTriangleIcon)`
  color: #c9190b;
  margin-left: 20px;
`;

function ScheduleListItem({
  rowIndex,
  isSelected,
  onSelect,
  schedule,
  isMissingInventory,
  isMissingSurvey,
}) {
  const labelId = `check-action-${schedule.id}`;

  const jobTypeLabels = {
    inventory_update: t`Inventory Sync`,
    job: t`Playbook Run`,
    project_update: t`Source Control Update`,
    system_job: t`Management Job`,
    workflow_job: t`Workflow Job`,
  };

  let scheduleBaseUrl;
  let relatedResourceUrl;

  switch (schedule.summary_fields.unified_job_template.unified_job_type) {
    case 'inventory_update':
      scheduleBaseUrl = `/inventories/inventory/${schedule.summary_fields.inventory.id}/sources/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      relatedResourceUrl = `/inventories/inventory/${schedule.summary_fields.inventory.id}/sources/${schedule.summary_fields.unified_job_template.id}/details`;
      break;
    case 'job':
      scheduleBaseUrl = `/templates/job_template/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      relatedResourceUrl = `/templates/job_template/${schedule.summary_fields.unified_job_template.id}/details`;
      break;
    case 'project_update':
      scheduleBaseUrl = `/projects/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      relatedResourceUrl = `/projects/${schedule.summary_fields.unified_job_template.id}/details`;
      break;
    case 'system_job':
      scheduleBaseUrl = `/management_jobs/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      relatedResourceUrl = `/management_jobs`;
      break;
    case 'workflow_job':
      scheduleBaseUrl = `/templates/workflow_job_template/${schedule.summary_fields.unified_job_template.id}/schedules/${schedule.id}`;
      relatedResourceUrl = `/templates/workflow_job_template/${schedule.summary_fields.unified_job_template.id}/details`;
      break;
    default:
      break;
  }
  const isDisabled = Boolean(isMissingInventory || isMissingSurvey);

  return (
    <Tr
      id={`schedule-row-${schedule.id}`}
      ouiaId={`schedule-row-${schedule.id}`}
    >
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
          disable: false,
        }}
        dataLabel={t`Selected`}
      />
      <TdBreakWord id={labelId} dataLabel={t`Name`}>
        <Link to={`${scheduleBaseUrl}/details`}>
          <b>{schedule.name}</b>
        </Link>
        {Boolean(isMissingInventory || isMissingSurvey) && (
          <span>
            <Tooltip
              content={[isMissingInventory, isMissingSurvey].map((message) =>
                message ? <div key={message}>{message}</div> : null
              )}
              position="right"
            >
              <ExclamationTriangleIcon />
            </Tooltip>
          </span>
        )}
      </TdBreakWord>
      <TdBreakWord
        id={`related-resource-${schedule.id}`}
        dataLabel={t`Related resource`}
      >
        <Link to={`${relatedResourceUrl}`}>
          <b>{schedule.summary_fields.unified_job_template.name}</b>
        </Link>
      </TdBreakWord>
      <Td dataLabel={t`Resource type`}>
        {
          jobTypeLabels[
            schedule.summary_fields.unified_job_template.unified_job_type
          ]
        }
      </Td>
      <Td dataLabel={t`Next Run`}>
        {schedule.next_run && (
          <DetailList stacked>
            <Detail
              label={t`Next Run`}
              value={formatDateString(schedule.next_run, schedule.timezone)}
            />
          </DetailList>
        )}
      </Td>
      <ActionsTd dataLabel={t`Actions`} gridColumns="auto 40px">
        <ScheduleToggle schedule={schedule} isDisabled={isDisabled} />
        <ActionItem
          visible={schedule.summary_fields.user_capabilities.edit}
          tooltip={t`Edit Schedule`}
        >
          <Button
            ouiaId={`${schedule.id}-edit-button`}
            aria-label={t`Edit Schedule`}
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

export default ScheduleListItem;
