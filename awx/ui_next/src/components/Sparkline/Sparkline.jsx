import React, { Fragment } from 'react';
import { arrayOf, object } from 'prop-types';
import { withI18n } from '@lingui/react';
import { JobStatusIcon as _JobStatusIcon } from '@components/Sparkline';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

const JobStatusIcon = styled(props => <_JobStatusIcon {...props} />)`
  margin-right: 5px;
`;

const Sparkline = ({ i18n, jobs }) => {
  const generateTooltip = (job) => (
    <Fragment>
      <div>{i18n._(t`JOB ID:`)} {job.id}</div>
      <div>{i18n._(t`STATUS:`)} {job.status.toUpperCase()}</div>
      <div>{i18n._(t`FINISHED:`)} {job.finished}</div>
    </Fragment>
  );

  return (
    (jobs.map(job => (
      <JobStatusIcon
        key={job.id}
        job={job}
        link={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}
        tooltip={generateTooltip(job)}
      />
    )))
  )
};

Sparkline.propTypes = {
  jobs: arrayOf(object),
};
Sparkline.defaultProps = {
  jobs: [],
};

export default withI18n()(Sparkline);
