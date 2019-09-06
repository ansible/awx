import React from 'react';
import { string } from 'prop-types';
import {
  ChangedBottom,
  ChangedTop,
  FailedBottom,
  FailedTop,
  FinishedJob,
  SkippedBottom,
  SkippedTop,
  SuccessfulBottom,
  SuccessfulTop,
  UnreachableBottom,
  UnreachableTop,
} from './shared/StatusIcon';

const HostStatusIcon = ({ status }) => {
  return (
    <div>
      {status === 'changed' && (
        <FinishedJob>
          <ChangedTop />
          <ChangedBottom />
        </FinishedJob>
      )}
      {status === 'failed' && (
        <FinishedJob>
          <FailedTop />
          <FailedBottom />
        </FinishedJob>
      )}
      {status === 'skipped' && (
        <FinishedJob>
          <SkippedTop />
          <SkippedBottom />
        </FinishedJob>
      )}
      {status === 'ok' && (
        <FinishedJob>
          <SuccessfulTop />
          <SuccessfulBottom />
        </FinishedJob>
      )}
      {status === 'unreachable' && (
        <FinishedJob>
          <UnreachableTop />
          <UnreachableBottom />
        </FinishedJob>
      )}
    </div>
  );
};

HostStatusIcon.propTypes = {
  status: string.isRequired,
};

export default HostStatusIcon;
