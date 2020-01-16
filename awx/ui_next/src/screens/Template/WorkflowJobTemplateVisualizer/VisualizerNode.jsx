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

const NodeG = styled.g`
  pointer-events: ${props => (props.noPointerEvents ? 'none' : 'initial')};
  cursor: ${props => (props.job ? 'pointer' : 'default')};
`;

const NodeContents = styled.foreignObject`
  font-size: 13px;
  padding: 0px 10px;
  background-color: ${props =>
    props.isInvalidLinkTarget ? '#D7D7D7' : '#FFFFFF'};
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
  onStartAddLinkClick,
  onConfirmAddLinkClick,
  addingLink,
  onMouseOver,
  isAddLinkSourceNode,
  onAddNodeClick,
  onEditNodeClick,
  onViewNodeClick,
}) {
  const [hovering, setHovering] = useState(false);

  const handleNodeMouseEnter = () => {
    const nodeEl = document.getElementById(`node-${node.id}`);
    nodeEl.parentNode.appendChild(nodeEl);
    setHovering(true);
    if (addingLink) {
      updateHelpText(
        node.isInvalidLinkTarget
          ? i18n._(
              t`Invalid link target.  Unable to link to children or ancestor nodes.  Graph cycles are not supported.`
            )
          : i18n._(t`Click to create a new link to this node.`)
      );
      onMouseOver(node);
    }
  };

  const handleNodeMouseLeave = () => {
    setHovering(false);
    if (addingLink) {
      updateHelpText(null);
    }
  };

  const handleNodeClick = () => {
    if (addingLink && !node.isInvalidLinkTarget && !isAddLinkSourceNode) {
      onConfirmAddLinkClick(node);
    }
  };

  const viewDetailsAction = (
    <WorkflowActionTooltipItem
      id="node-details"
      key="details"
      onMouseEnter={() => updateHelpText(i18n._(t`View node details`))}
      onMouseLeave={() => updateHelpText(null)}
      onClick={() => {
        updateHelpText(null);
        setHovering(false);
        onViewNodeClick(node);
      }}
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
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onAddNodeClick(node.id);
          }}
        >
          <PlusIcon />
        </WorkflowActionTooltipItem>,
        viewDetailsAction,
        <WorkflowActionTooltipItem
          id="node-edit"
          key="edit"
          onMouseEnter={() => updateHelpText(i18n._(t`Edit this node`))}
          onMouseLeave={() => updateHelpText(null)}
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onEditNodeClick(node);
          }}
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
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onStartAddLinkClick(node);
          }}
        >
          <LinkIcon />
        </WorkflowActionTooltipItem>,
        <WorkflowActionTooltipItem
          id="node-delete"
          key="delete"
          onMouseEnter={() => updateHelpText(i18n._(t`Delete this node`))}
          onMouseLeave={() => updateHelpText(null)}
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onDeleteNodeClick(node);
          }}
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
      noPointerEvents={isAddLinkSourceNode}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={handleNodeMouseLeave}
    >
      <rect
        width={wfConstants.nodeW}
        height={wfConstants.nodeH}
        rx="2"
        ry="2"
        stroke={
          hovering && addingLink && !node.isInvalidLinkTarget
            ? '#007ABC'
            : '#93969A'
        }
        strokeWidth="4px"
        fill="#FFFFFF"
      />
      <NodeContents
        height="60"
        width="180"
        isInvalidLinkTarget={node.isInvalidLinkTarget}
        {...(!addingLink && {
          onMouseEnter: () => updateNodeHelp(node),
          onMouseLeave: () => updateNodeHelp(null),
        })}
        onClick={() => handleNodeClick()}
      >
        <NodeDefaultLabel>
          {node.unifiedJobTemplate
            ? node.unifiedJobTemplate.name
            : i18n._(t`DELETED`)}
        </NodeDefaultLabel>
      </NodeContents>
      {node.unifiedJobTemplate && <WorkflowNodeTypeLetter node={node} />}
      {hovering && !addingLink && (
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
