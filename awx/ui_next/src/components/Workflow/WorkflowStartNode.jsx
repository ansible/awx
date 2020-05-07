import React, { useContext, useRef, useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { bool, func } from 'prop-types';
import { PlusIcon } from '@patternfly/react-icons';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../contexts/Workflow';
import { constants as wfConstants } from './WorkflowUtils';
import WorkflowActionTooltip from './WorkflowActionTooltip';
import WorkflowActionTooltipItem from './WorkflowActionTooltipItem';

const StartG = styled.g`
  pointer-events: ${props => (props.ignorePointerEvents ? 'none' : 'auto')};
`;

function WorkflowStartNode({ i18n, onUpdateHelpText, showActionTooltip }) {
  const ref = useRef(null);
  const [hovering, setHovering] = useState(false);
  const dispatch = useContext(WorkflowDispatchContext);
  const { addingLink, nodePositions } = useContext(WorkflowStateContext);

  const handleNodeMouseEnter = () => {
    ref.current.parentNode.appendChild(ref.current);
    setHovering(true);
  };

  return (
    <StartG
      id="node-1"
      ignorePointerEvents={addingLink}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={() => setHovering(false)}
      ref={ref}
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
      {showActionTooltip && hovering && (
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
                dispatch({ type: 'START_ADD_NODE', sourceNodeId: 1 });
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

WorkflowStartNode.propTypes = {
  showActionTooltip: bool.isRequired,
  onUpdateHelpText: func,
};

WorkflowStartNode.defaultProps = {
  onUpdateHelpText: () => {},
};

export default withI18n()(WorkflowStartNode);
