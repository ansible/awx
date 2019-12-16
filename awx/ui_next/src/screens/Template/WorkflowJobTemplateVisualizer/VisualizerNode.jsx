import React, { useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  InfoIcon,
  LinkIcon,
  PencilAltIcon,
  PlusIcon,
  TrashAltIcon,
} from '@patternfly/react-icons';
import { constants as wfConstants } from '@util/workflow';
import {
  WorkflowActionTooltip,
  WorkflowActionTooltipItem,
  WorkflowNodeTypeLetter,
} from '@components/Workflow';

// dont need this in this component
const NodeG = styled.g`
  cursor: ${props => (props.job ? 'pointer' : 'default')};
`;

const NodeContents = styled.foreignObject`
  font-size: 13px;
  padding: 0px 10px;
`;

const NodeDefaultLabel = styled.p`
  margin-top: 20px;
  text-align: center;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
`;

function VisualizerNode({
  node,
  nodePositions,
  updateHelpText,
  updateNodeHelp,
  readOnly,
  i18n,
  onDeleteNodeClick,
}) {
  const [hovering, setHovering] = useState(false);

  const handleNodeMouseEnter = () => {
    const nodeEl = document.getElementById(`node-${node.id}`);
    nodeEl.parentNode.appendChild(nodeEl);
    setHovering(true);
  };

  const viewDetailsAction = (
    <WorkflowActionTooltipItem
      id="node-details"
      key="details"
      onMouseEnter={() => updateHelpText(i18n._(t`View node details`))}
      onMouseLeave={() => updateHelpText(null)}
    >
      <InfoIcon />
    </WorkflowActionTooltipItem>
  );

  const tooltipActions = readOnly
    ? [viewDetailsAction]
    : [
        <WorkflowActionTooltipItem
          id="node-add"
          key="add"
          onMouseEnter={() => updateHelpText(i18n._(t`Add a new node`))}
          onMouseLeave={() => updateHelpText(null)}
        >
          <PlusIcon />
        </WorkflowActionTooltipItem>,
        viewDetailsAction,
        <WorkflowActionTooltipItem
          id="node-edit"
          key="edit"
          onMouseEnter={() => updateHelpText(i18n._(t`Edit this node`))}
          onMouseLeave={() => updateHelpText(null)}
        >
          <PencilAltIcon />
        </WorkflowActionTooltipItem>,
        <WorkflowActionTooltipItem
          id="node-link"
          key="link"
          onMouseEnter={() =>
            updateHelpText(i18n._(t`Link to an available node`))
          }
          onMouseLeave={() => updateHelpText(null)}
        >
          <LinkIcon />
        </WorkflowActionTooltipItem>,
        <WorkflowActionTooltipItem
          id="node-delete"
          key="delete"
          onMouseEnter={() => updateHelpText(i18n._(t`Delete this node`))}
          onMouseLeave={() => updateHelpText(null)}
          onClick={() => onDeleteNodeClick(node)}
        >
          <TrashAltIcon />
        </WorkflowActionTooltipItem>,
      ];

  return (
    <NodeG
      id={`node-${node.id}`}
      transform={`translate(${nodePositions[node.id].x},${nodePositions[node.id]
        .y - nodePositions[1].y})`}
      job={node.job}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={() => setHovering(false)}
    >
      <rect
        width={wfConstants.nodeW}
        height={wfConstants.nodeH}
        rx="2"
        ry="2"
        stroke="#93969A"
        strokeWidth="2px"
        fill="#FFFFFF"
      />
      <NodeContents
        height="60"
        width="180"
        onMouseEnter={() => updateNodeHelp(node)}
        onMouseLeave={() => updateNodeHelp(null)}
      >
        <NodeDefaultLabel>
          {node.unifiedJobTemplate
            ? node.unifiedJobTemplate.name
            : i18n._(t`DELETED`)}
        </NodeDefaultLabel>
      </NodeContents>
      {node.unifiedJobTemplate && <WorkflowNodeTypeLetter node={node} />}
      {hovering && (
        <WorkflowActionTooltip
          pointX={wfConstants.nodeW}
          pointY={wfConstants.nodeH / 2}
          actions={tooltipActions}
        />
      )}
    </NodeG>
  );
}

export default withI18n()(VisualizerNode);
