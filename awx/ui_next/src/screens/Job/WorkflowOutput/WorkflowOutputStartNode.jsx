import React from 'react';
import { shape } from 'prop-types';
import { constants as wfConstants } from '@util/workflow';

function WorkflowOutputStartNode({ nodePositions }) {
  return (
    <g id="node-1" transform={`translate(${nodePositions[1].x},0)`}>
      <rect
        fill="#0279BC"
        height={wfConstants.rootH}
        rx="2"
        ry="2"
        width={wfConstants.rootW}
        y="10"
      />
      {/* TODO: We need to be able to handle translated text here */}
      <text x="13" y="30" dy=".35em" fill="white">
        START
      </text>
    </g>
  );
}

WorkflowOutputStartNode.propTypes = {
  nodePositions: shape().isRequired,
};

export default WorkflowOutputStartNode;
