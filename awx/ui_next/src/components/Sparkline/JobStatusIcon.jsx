import React, { Fragment } from 'react';
import { node, number, shape, string } from 'prop-types';
import { Link } from 'react-router-dom';
import styled, { keyframes } from 'styled-components';
import { Tooltip } from '@patternfly/react-core';

const Pulse = keyframes`
  from {
    -webkit-transform:scale(1);
  }
  to {
    -webkit-transform:scale(0);
  }
`;

const Wrapper = styled.div`
  width: 14px;
  height: 14px;
`;

const RunningJob = styled(Wrapper)`
  background-color: #5cb85c;
  padding-right: 0px;
  text-shadow: -1px -1px 0 #ffffff, 1px -1px 0 #ffffff, -1px 1px 0 #ffffff,
    1px 1px 0 #ffffff;
  animation: ${Pulse} 1.5s linear infinite alternate;
`;

const WaitingJob = styled(Wrapper)`
  border: 1px solid #d7d7d7;
`;

const FinishedJob = styled(Wrapper)`
  flex: 0 1 auto;
  > * {
    width: 14px;
    height: 7px;
  }
`;

const SuccessfulTop = styled.div`
  background-color: #5cb85c;
`;

const SuccessfulBottom = styled.div`
  border: 1px solid #b7b7b7;
  border-top: 0;
  background: #ffffff;
`;

const FailedTop = styled.div`
  border: 1px solid #b7b7b7;
  border-bottom: 0;
  background: #ffffff;
`;

const FailedBottom = styled.div`
  background-color: #d9534f;
`;

const JobStatusIcon = ({ job, link, tooltip, ...props }) => {
  let Icon = (
    <Fragment>
      {job.status === 'running' && <RunningJob />}
      {(job.status === 'new' ||
        job.status === 'pending' ||
        job.status === 'waiting') && <WaitingJob />}
      {(job.status === 'failed' ||
        job.status === 'error' ||
        job.status === 'canceled') && (
        <FinishedJob>
          <FailedTop />
          <FailedBottom />
        </FinishedJob>
      )}
      {job.status === 'successful' && (
        <FinishedJob>
          <SuccessfulTop />
          <SuccessfulBottom />
        </FinishedJob>
      )}
    </Fragment>
  );

  if (link) {
    Icon = <Link to={link}>{Icon}</Link>;
  }

  if (tooltip) {
    return (
      <div {...props}>
        <Tooltip position="top" content={tooltip}>
          {Icon}
        </Tooltip>
      </div>
    );
  }

  return <div {...props}>{Icon}</div>;
};

JobStatusIcon.propTypes = {
  job: shape({
    id: number.isRequired,
    status: string.isRequired,
  }).isRequired,
  link: string,
  tooltip: node,
};

JobStatusIcon.defaultProps = {
  link: null,
  tooltip: null,
};

export default JobStatusIcon;
