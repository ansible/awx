import React, { Fragment } from 'react';
import { arrayOf, object } from 'prop-types';
import { withI18n } from '@lingui/react';
import { Link as _Link } from 'react-router-dom';
import { StatusIcon } from '@components/Sparkline';
import { Tooltip } from '@patternfly/react-core';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

/* eslint-disable react/jsx-pascal-case */
const Link = styled(props => <_Link {...props} />)`
  margin-right: 5px;
`;
/* eslint-enable react/jsx-pascal-case */

const Sparkline = ({ i18n, jobs }) => {
  const generateTooltip = job => (
    <Fragment>
      <div>
        {i18n._(t`JOB ID:`)} {job.id}
      </div>
      <div>
        {i18n._(t`STATUS:`)} {job.status.toUpperCase()}
      </div>
      {job.finished && (
        <div>
          {i18n._(t`FINISHED:`)} {job.finished}
        </div>
      )}
    </Fragment>
  );

  return jobs.map(job => (
    <Tooltip position="top" content={generateTooltip(job)} key={job.id}>
      <Link to={`/jobs/${JOB_TYPE_URL_SEGMENTS[job.type]}/${job.id}`}>
        <StatusIcon status={job.status} />
      </Link>
    </Tooltip>
  ));
};

Sparkline.propTypes = {
  jobs: arrayOf(object),
};
Sparkline.defaultProps = {
  jobs: [],
};

export default withI18n()(Sparkline);
