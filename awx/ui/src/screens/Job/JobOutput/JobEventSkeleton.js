import React, { useEffect } from 'react';
import {
  JobEventLine,
  JobEventLineToggle,
  JobEventLineNumber,
  JobEventLineText,
} from './shared';

function JobEventSkeletonContent({ contentLength }) {
  return (
    <JobEventLineText>
      <span className="content">{' '.repeat(contentLength)}</span>
    </JobEventLineText>
  );
}

function JobEventSkeleton({ counter, contentLength, style, measure }) {
  useEffect(() => {
    measure();
  }, [measure]);

  return (
    counter > 1 && (
      <div style={style}>
        <JobEventLine key={counter}>
          <JobEventLineToggle />
          <JobEventLineNumber />
          <JobEventSkeletonContent contentLength={contentLength} />
        </JobEventLine>
      </div>
    )
  );
}

export default JobEventSkeleton;
