import React from 'react';
import { constants as wfConstants } from '@util/workflow';

function WorkflowOutputStartNode({ nodePositions }) {
  return (
    <g id="node-1" transform={`translate(${nodePositions[1].x},0)`}>
      <rect
        width={wfConstants.rootW}
        height={wfConstants.rootH}
        y="10"
        rx="2"
        ry="2"
        fill="#0279BC"
      />
      {/* TODO: Translate this...? */}
      <text x="13" y="30" dy=".35em" fill="white">
        START
      </text>
    </g>
  );
}

export default WorkflowOutputStartNode;
