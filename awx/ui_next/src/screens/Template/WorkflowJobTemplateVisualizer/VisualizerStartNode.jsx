import React, { useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PlusIcon } from '@patternfly/react-icons';
import { constants as wfConstants } from '@util/workflow';
import {
  WorkflowActionTooltip,
  WorkflowActionTooltipItem,
} from '@components/Workflow';

const StartG = styled.g`
  pointer-events: ${props => (props.ignorePointerEvents ? 'none' : 'auto')};
`;

function VisualizerStartNode({
  updateHelpText,
  nodePositions,
  readOnly,
  i18n,
  addingLink,
  onAddNodeClick,
}) {
  const [hovering, setHovering] = useState(false);

  const handleNodeMouseEnter = () => {
    const nodeEl = document.getElementById('node-1');
    nodeEl.parentNode.appendChild(nodeEl);
    setHovering(true);
  };

  return (
    <StartG
      id="node-1"
      transform={`translate(${nodePositions[1].x},0)`}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={() => setHovering(false)}
      ignorePointerEvents={addingLink}
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
              onClick={() => {
                updateHelpText(null);
                setHovering(false);
                onAddNodeClick(1);
              }}
            >
              <PlusIcon />
            </WorkflowActionTooltipItem>,
          ]}
        />
      )}
    </StartG>
  );
}

export default withI18n()(VisualizerStartNode);
