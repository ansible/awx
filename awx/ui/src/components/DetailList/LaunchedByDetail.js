import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import getScheduleUrl from 'util/getScheduleUrl';
import Detail from './Detail';

const getLaunchedByDetails = (job) => {
  const {
    created_by: createdBy,
    job_template: jobTemplate,
    workflow_job_template: workflowJT,
    schedule,
  } = job.summary_fields;

  if (!createdBy && !schedule) {
    return {};
  }

  let link;
  let value;

  switch (job.launch_type) {
    case 'webhook':
      value = t`Webhook`;
      link =
        (jobTemplate && `/templates/job_template/${jobTemplate.id}/details`) ||
        (workflowJT &&
          `/templates/workflow_job_template/${workflowJT.id}/details`);
      break;
    case 'scheduled':
      value = schedule.name;
      link = getScheduleUrl(job);
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

export default function LaunchedByDetail({ job, dataCy = null }) {
  const { value: launchedByValue, link: launchedByLink } =
    getLaunchedByDetails(job) || {};

  return (
    <Detail
      dataCy={dataCy}
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
