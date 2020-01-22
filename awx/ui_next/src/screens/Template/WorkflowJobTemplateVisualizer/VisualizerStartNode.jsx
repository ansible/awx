import React, { useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { bool, func, shape } from 'prop-types';
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
  addingLink,
  i18n,
  nodePositions,
  onAddNodeClick,
  onUpdateHelpText,
  readOnly,
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
      ignorePointerEvents={addingLink}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={() => setHovering(false)}
      transform={`translate(${nodePositions[1].x},0)`}
    >
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
      {!readOnly && hovering && (
        <WorkflowActionTooltip
          actions={[
            <WorkflowActionTooltipItem
              id="node-add"
              key="add"
              onMouseEnter={() => onUpdateHelpText(i18n._(t`Add a new node`))}
              onMouseLeave={() => onUpdateHelpText(null)}
              onClick={() => {
                onUpdateHelpText(null);
                setHovering(false);
                onAddNodeClick(1);
              }}
            >
              <PlusIcon />
            </WorkflowActionTooltipItem>,
          ]}
          pointX={wfConstants.rootW}
          pointY={wfConstants.rootH / 2 + 10}
        />
      )}
    </StartG>
  );
}

VisualizerStartNode.propTypes = {
  addingLink: bool.isRequired,
  nodePositions: shape().isRequired,
  onAddNodeClick: func.isRequired,
  readOnly: bool.isRequired,
  onUpdateHelpText: func.isRequired,
};

export default withI18n()(VisualizerStartNode);
