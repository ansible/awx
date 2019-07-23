import styled from 'styled-components';
import React from 'react';

const JobEventSkeletonWrapper = styled.div``;
const JobEventSkeletonLine = styled.div`
  display: flex;

  &:hover {
    background-color: white;
  }

  &:hover div {
    background-color: white;
  }

  &--hidden {
    display: none;
  }
`;
const JobEventSkeletonLineToggle = styled.div`
  background-color: #ebebeb;
  color: #646972;
  display: flex;
  flex: 0 0 30px;
  font-size: 18px;
  justify-content: center;
  line-height: 12px;

  & > i {
    cursor: pointer;
  }

  user-select: none;
`;
const JobEventSkeletonLineNumber = styled.div`
  color: #161b1f;
  background-color: #ebebeb;
  flex: 0 0 45px;
  text-align: right;
  vertical-align: top;
  padding-right: 5px;
  border-right: 1px solid #b7b7b7;
  user-select: none;
`;
const JobEventSkeletonContentWrapper = styled.div`
  padding: 0 15px;
  white-space: pre-wrap;
  word-break: break-all;
  word-wrap: break-word;

  .content {
    background: var(--pf-global--disabled-color--200);
    background: linear-gradient(
      to right,
      #f5f5f5 10%,
      #e8e8e8 18%,
      #f5f5f5 33%
    );
    border-radius: 5px;
  }
`;

function JobEventSkeletonContent({ contentLength }) {
  return (
    <JobEventSkeletonContentWrapper>
      <span className="content">{' '.repeat(contentLength)}</span>
    </JobEventSkeletonContentWrapper>
  );
}

function JobEventSkeleton({ counter, contentLength, ...rest }) {
  return (
    counter > 1 && (
      <JobEventSkeletonWrapper {...rest}>
        <JobEventSkeletonLine key={counter}>
          <JobEventSkeletonLineToggle />
          <JobEventSkeletonLineNumber />
          <JobEventSkeletonContent contentLength={contentLength} />
        </JobEventSkeletonLine>
      </JobEventSkeletonWrapper>
    )
  );
}

export default JobEventSkeleton;
