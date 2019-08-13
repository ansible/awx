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
