import React, { useContext, useRef, useState } from 'react';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { bool, func } from 'prop-types';
import { PlusIcon } from '@patternfly/react-icons';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import WorkflowActionTooltip from './WorkflowActionTooltip';
import WorkflowActionTooltipItem from './WorkflowActionTooltipItem';

const StartG = styled.g`
  pointer-events: ${(props) => (props.ignorePointerEvents ? 'none' : 'auto')};
`;

const StartForeignObject = styled.foreignObject`
  overflow: visible;
`;

const StartDiv = styled.div`
  background-color: #0279bc;
  color: white;
  width: max-content;
  min-width: 80px;
  height: 40px;
  border-radius: 0.35em;
  text-align: center;
  line-height: 40px;
  padding: 0px 10px;
`;

function WorkflowStartNode({ onUpdateHelpText, showActionTooltip }) {
  const ref = useRef(null);
  const startNodeRef = useRef(null);
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
      <StartForeignObject
        height="1"
        width="1"
        y="10"
        style={{ overflow: 'visible' }}
      >
        <StartDiv ref={startNodeRef}>{t`START`}</StartDiv>
      </StartForeignObject>
      {showActionTooltip && hovering && (
        <WorkflowActionTooltip
          actions={[
            <WorkflowActionTooltipItem
              id="node-add"
              key="add"
              onMouseEnter={() => onUpdateHelpText(t`Add a new node`)}
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
          pointX={startNodeRef.current.offsetWidth}
          pointY={startNodeRef.current.offsetHeight / 2 + 10}
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

export default WorkflowStartNode;
