import React from 'react';
import { Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import Detail from './Detail';

const getLaunchedByDetails = ({ summary_fields = {}, related = {} }) => {
  const {
    created_by: createdBy,
    job_template: jobTemplate,
    schedule,
  } = summary_fields;
  const { schedule: relatedSchedule } = related;

  if (!createdBy && !schedule) {
    return {};
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

export default function LaunchedByDetail({ job, i18n }) {
  const { value: launchedByValue, link: launchedByLink } =
    getLaunchedByDetails(job) || {};

  return (
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
  );
}
