import React from 'react';
import { string } from 'prop-types';
import {
  RunningJob,
  WaitingJob,
  FinishedJob,
  SuccessfulTop,
  SuccessfulBottom,
  FailedBottom,
  FailedTop,
} from './shared/StatusIcon';

const JobStatusIcon = ({ status, ...props }) => {
  return (
    <div {...props}>
      {status === 'running' && <RunningJob />}
      {(status === 'new' || status === 'pending' || status === 'waiting') && (
        <WaitingJob />
      )}
      {(status === 'failed' || status === 'error' || status === 'canceled') && (
        <FinishedJob>
          <FailedTop />
          <FailedBottom />
        </FinishedJob>
      )}
      {status === 'successful' && (
        <FinishedJob>
          <SuccessfulTop />
          <SuccessfulBottom />
        </FinishedJob>
      )}
    </div>
  );
};

JobStatusIcon.propTypes = {
  status: string.isRequired,
};

export default JobStatusIcon;
