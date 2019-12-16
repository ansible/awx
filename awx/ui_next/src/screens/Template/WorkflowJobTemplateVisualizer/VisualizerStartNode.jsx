import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { constants as wfConstants } from '@util/workflow';
import {
  WorkflowActionTooltip,
  WorkflowActionTooltipItem,
} from '@components/Workflow';

function VisualizerStartNode({
  updateHelpText,
  nodePositions,
  readOnly,
  i18n,
}) {
  const [hovering, setHovering] = useState(false);

  const handleNodeMouseEnter = () => {
    const nodeEl = document.getElementById('node-1');
    nodeEl.parentNode.appendChild(nodeEl);
    setHovering(true);
  };

  return (
    <g
      id="node-1"
      transform={`translate(${nodePositions[1].x},0)`}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={() => setHovering(false)}
    >
      <rect
        width={wfConstants.rootW}
        height={wfConstants.rootH}
        y="10"
        rx="2"
        ry="2"
        fill="#0279BC"
      />
      {/* TODO: We need to be able to handle translated text here */}
      <text x="13" y="30" dy=".35em" fill="white">
        START
      </text>
      {!readOnly && hovering && (
        <WorkflowActionTooltip
          pointX={wfConstants.rootW}
          pointY={wfConstants.rootH / 2 + 10}
          actions={[
            <WorkflowActionTooltipItem
              id="node-add"
              key="add"
              onMouseEnter={() => updateHelpText(i18n._(t`Add a new node`))}
              onMouseLeave={() => updateHelpText(null)}
            >
              <i className="pf-icon pf-icon-add-circle-o" />
            </WorkflowActionTooltipItem>,
          ]}
        />
      )}
    </g>
  );
}

export default withI18n()(VisualizerStartNode);
