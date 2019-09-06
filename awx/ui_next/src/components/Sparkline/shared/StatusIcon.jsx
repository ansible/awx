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

export const RunningJob = styled(Wrapper)`
  background-color: #5cb85c;
  padding-right: 0px;
  text-shadow: -1px -1px 0 #ffffff, 1px -1px 0 #ffffff, -1px 1px 0 #ffffff,
    1px 1px 0 #ffffff;
  animation: ${Pulse} 1.5s linear infinite alternate;
`;

export const WaitingJob = styled(Wrapper)`
  border: 1px solid #d7d7d7;
`;

export const FinishedJob = styled(Wrapper)`
  flex: 0 1 auto;
  > * {
    width: 14px;
    height: 7px;
  }
`;

export const SuccessfulTop = styled.div`
  background-color: #5cb85c;
`;
export const SuccessfulBottom = styled(WhiteBottom)``;

export const FailedTop = styled(WhiteTop)``;
export const FailedBottom = styled.div`
  background-color: #d9534f;
`;

export const UnreachableTop = styled(WhiteTop)``;
export const UnreachableBottom = styled.div`
  background-color: #ff0000;
`;

export const ChangedTop = styled(WhiteTop)``;
export const ChangedBottom = styled.div`
  background-color: #ff9900;
`;

export const SkippedTop = styled(WhiteTop)``;
export const SkippedBottom = styled.div`
  background-color: #2dbaba;
`;
