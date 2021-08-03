import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import Detail from './Detail';

function getScheduleURL(template, scheduleId, inventoryId = null) {
  let scheduleUrl;

  switch (template.unified_job_type) {
    case 'inventory_update':
      scheduleUrl =
        inventoryId &&
        `/inventories/inventory/${inventoryId}/sources/${template.id}/schedules/${scheduleId}/details`;
      break;
    case 'job':
      scheduleUrl = `/templates/job_template/${template.id}/schedules/${scheduleId}/details`;
      break;
    case 'project_update':
      scheduleUrl = `/projects/${template.id}/schedules/${scheduleId}/details`;
      break;
    case 'system_job':
      scheduleUrl = `/management_jobs/${template.id}/schedules/${scheduleId}/details`;
      break;
    case 'workflow_job':
      scheduleUrl = `/templates/workflow_job_template/${template.id}/schedules/${scheduleId}/details`;
      break;
    default:
      break;
  }

  return scheduleUrl;
}

const getLaunchedByDetails = ({ summary_fields = {}, launch_type }) => {
  const {
    created_by: createdBy,
    job_template: jobTemplate,
    unified_job_template: unifiedJT,
    workflow_job_template: workflowJT,
    inventory,
    schedule,
  } = summary_fields;

  if (!createdBy && !schedule) {
    return {};
  }

  let link;
  let value;

  switch (launch_type) {
    case 'webhook':
      value = t`Webhook`;
      link =
        (jobTemplate && `/templates/job_template/${jobTemplate.id}/details`) ||
        (workflowJT &&
          `/templates/workflow_job_template/${workflowJT.id}/details`);
      break;
    case 'scheduled':
      value = schedule.name;
      link = getScheduleURL(unifiedJT, schedule.id, inventory?.id);
      break;
    case 'manual':
      link = `/users/${createdBy.id}/details`;
      value = createdBy.username;
      break;
    default:
      link = createdBy && `/users/${createdBy.id}/details`;
      value = createdBy && createdBy.username;
      break;
  }

  return { link, value };
};

export default function LaunchedByDetail({ job }) {
  const { value: launchedByValue, link: launchedByLink } =
    getLaunchedByDetails(job) || {};

  return (
    <Detail
      label={t`Launched By`}
      value={
        launchedByLink ? (
          <Link to={`${launchedByLink}`}>{launchedByValue}</Link>
        ) : (
          launchedByValue
        )
      }
    />
  );
}
