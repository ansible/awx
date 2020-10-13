import React from 'react';
import { string } from 'prop-types';
import styled, { keyframes } from 'styled-components';

const Pulse = keyframes`
  from {
    -webkit-transform:scale(1);
  }
  to {
    -webkit-transform:scale(0);
  }
`;

const Wrapper = styled.div`
  align-items: center;
  display: flex;
  flex-flow: column nowrap;
  height: 14px;
  margin: 5px 0;
  width: 14px;
`;

const WhiteTop = styled.div`
  border: 1px solid #b7b7b7;
  border-bottom: 0;
  background: #ffffff;
`;

const WhiteBottom = styled.div`
  border: 1px solid #b7b7b7;
  border-top: 0;
  background: #ffffff;
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
const SuccessfulBottom = styled(WhiteBottom)``;

const FailedTop = styled(WhiteTop)``;
const FailedBottom = styled.div`
  background-color: #d9534f;
`;

const UnreachableTop = styled(WhiteTop)``;
const UnreachableBottom = styled.div`
  background-color: #ff0000;
`;

const ChangedTop = styled(WhiteTop)``;
const ChangedBottom = styled.div`
  background-color: #ff9900;
`;

const SkippedTop = styled(WhiteTop)``;
const SkippedBottom = styled.div`
  background-color: #2dbaba;
`;

RunningJob.displayName = 'RunningJob';
WaitingJob.displayName = 'WaitingJob';
FinishedJob.displayName = 'FinishedJob';
SuccessfulTop.displayName = 'SuccessfulTop';
SuccessfulBottom.displayName = 'SuccessfulBottom';
FailedTop.displayName = 'FailedTop';
FailedBottom.displayName = 'FailedBottom';
UnreachableTop.displayName = 'UnreachableTop';
UnreachableBottom.displayName = 'UnreachableBottom';
ChangedTop.displayName = 'ChangedTop';
ChangedBottom.displayName = 'ChangedBottom';
SkippedTop.displayName = 'SkippedTop';
SkippedBottom.displayName = 'SkippedBottom';

const StatusIcon = ({ status, ...props }) => {
  return (
    <div {...props} data-job-status={status} aria-label={status}>
      {status === 'running' && <RunningJob aria-hidden="true" />}
      {(status === 'new' ||
        status === 'pending' ||
        status === 'waiting' ||
        status === 'never updated') && <WaitingJob aria-hidden="true" />}
      {(status === 'failed' || status === 'error' || status === 'canceled') && (
        <FinishedJob aria-hidden="true">
          <FailedTop />
          <FailedBottom />
        </FinishedJob>
      )}
      {(status === 'successful' || status === 'ok') && (
        <FinishedJob aria-hidden="true">
          <SuccessfulTop />
          <SuccessfulBottom />
        </FinishedJob>
      )}
      {status === 'changed' && (
        <FinishedJob aria-hidden="true">
          <ChangedTop />
          <ChangedBottom />
        </FinishedJob>
      )}
      {status === 'skipped' && (
        <FinishedJob aria-hidden="true">
          <SkippedTop />
          <SkippedBottom />
        </FinishedJob>
      )}
      {status === 'unreachable' && (
        <FinishedJob aria-hidden="true">
          <UnreachableTop />
          <UnreachableBottom />
        </FinishedJob>
      )}
      <span className="pf-screen-reader"> {status} </span>
    </div>
  );
};

StatusIcon.propTypes = {
  status: string.isRequired,
};

export default StatusIcon;
