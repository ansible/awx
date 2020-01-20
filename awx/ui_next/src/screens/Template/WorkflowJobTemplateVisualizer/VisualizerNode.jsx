import React, { useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { bool, func, shape } from 'prop-types';
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
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

function VisualizerNode({
  addingLink,
  i18n,
  isAddLinkSourceNode,
  node,
  nodePositions,
  onAddNodeClick,
  onConfirmAddLinkClick,
  onDeleteNodeClick,
  onEditNodeClick,
  onMouseOver,
  onStartAddLinkClick,
  onViewNodeClick,
  readOnly,
  updateHelpText,
  updateNodeHelp,
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
      onClick={() => {
        updateHelpText(null);
        setHovering(false);
        onViewNodeClick(node);
      }}
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
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onAddNodeClick(node.id);
          }}
          onMouseEnter={() => updateHelpText(i18n._(t`Add a new node`))}
          onMouseLeave={() => updateHelpText(null)}
        >
          <PlusIcon />
        </WorkflowActionTooltipItem>,
        viewDetailsAction,
        <WorkflowActionTooltipItem
          id="node-edit"
          key="edit"
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onEditNodeClick(node);
          }}
          onMouseEnter={() => updateHelpText(i18n._(t`Edit this node`))}
          onMouseLeave={() => updateHelpText(null)}
        >
          <PencilAltIcon />
        </WorkflowActionTooltipItem>,
        <WorkflowActionTooltipItem
          id="node-link"
          key="link"
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onStartAddLinkClick(node);
          }}
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
          onClick={() => {
            updateHelpText(null);
            setHovering(false);
            onDeleteNodeClick(node);
          }}
          onMouseEnter={() => updateHelpText(i18n._(t`Delete this node`))}
          onMouseLeave={() => updateHelpText(null)}
        >
          <TrashAltIcon />
        </WorkflowActionTooltipItem>,
      ];

  return (
    <NodeG
      id={`node-${node.id}`}
      job={node.job}
      noPointerEvents={isAddLinkSourceNode}
      onMouseEnter={handleNodeMouseEnter}
      onMouseLeave={handleNodeMouseLeave}
      transform={`translate(${nodePositions[node.id].x},${nodePositions[node.id]
        .y - nodePositions[1].y})`}
    >
      <rect
        fill="#FFFFFF"
        height={wfConstants.nodeH}
        rx="2"
        ry="2"
        stroke={
          hovering && addingLink && !node.isInvalidLinkTarget
            ? '#007ABC'
            : '#93969A'
        }
        strokeWidth="4px"
        width={wfConstants.nodeW}
      />
      <NodeContents
        height="60"
        isInvalidLinkTarget={node.isInvalidLinkTarget}
        {...(!addingLink && {
          onMouseEnter: () => updateNodeHelp(node),
          onMouseLeave: () => updateNodeHelp(null),
        })}
        onClick={() => handleNodeClick()}
        width="180"
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

VisualizerNode.propTypes = {
  addingLink: bool.isRequired,
  isAddLinkSourceNode: bool,
  node: shape().isRequired,
  nodePositions: shape().isRequired,
  onAddNodeClick: func.isRequired,
  onConfirmAddLinkClick: func.isRequired,
  onDeleteNodeClick: func.isRequired,
  onEditNodeClick: func.isRequired,
  onMouseOver: func,
  onStartAddLinkClick: func.isRequired,
  onViewNodeClick: func.isRequired,
  readOnly: bool.isRequired,
  updateHelpText: func.isRequired,
  updateNodeHelp: func.isRequired,
};

VisualizerNode.defaultProps = {
  isAddLinkSourceNode: false,
  onMouseOver: () => {},
};

export default withI18n()(VisualizerNode);
