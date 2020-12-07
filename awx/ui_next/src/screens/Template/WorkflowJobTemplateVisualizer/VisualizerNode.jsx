import React, { useContext, useRef, useState } from 'react';
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
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import { WorkflowJobTemplateNodesAPI } from '../../../api';
import { constants as wfConstants } from '../../../components/Workflow/WorkflowUtils';
import {
  WorkflowActionTooltip,
  WorkflowActionTooltipItem,
  WorkflowNodeTypeLetter,
} from '../../../components/Workflow';
import getNodeType from './shared/WorkflowJobTemplateVisualizerUtils';

const NodeG = styled.g`
  pointer-events: ${props => (props.noPointerEvents ? 'none' : 'initial')};
  cursor: ${props => (props.job ? 'pointer' : 'default')};
`;

const NodeContents = styled.div`
  font-size: 13px;
  padding: 0px 10px;
  background-color: ${props =>
    props.isInvalidLinkTarget ? '#D7D7D7' : '#FFFFFF'};
`;

const NodeResourceName = styled.p`
  margin-top: 20px;
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
`;
NodeResourceName.displayName = 'NodeResourceName';

function VisualizerNode({
  i18n,
  node,
  onMouseOver,
  readOnly,
  updateHelpText,
  updateNodeHelp,
}) {
  const ref = useRef(null);
  const [hovering, setHovering] = useState(false);
  const [credentialsError, setCredentialsError] = useState(null);
  const [detailError, setDetailError] = useState(null);
  const dispatch = useContext(WorkflowDispatchContext);
  const { addingLink, addLinkSourceNode, nodePositions, nodes } = useContext(
    WorkflowStateContext
  );
  const isAddLinkSourceNode =
    addLinkSourceNode && addLinkSourceNode.id === node.id;

  const handleCredentialsErrorClose = () => setCredentialsError(null);
  const handleDetailErrorClose = () => setDetailError(null);

  const updateNode = async () => {
    const updatedNodes = [...nodes];
    const updatedNode = updatedNodes.find(n => n.id === node.id);
    if (
      !node.fullUnifiedJobTemplate &&
      node?.originalNodeObject?.summary_fields?.unified_job_template
    ) {
      const [, nodeAPI] = getNodeType(
        node.originalNodeObject.summary_fields.unified_job_template
      );
      try {
        const { data: fullUnifiedJobTemplate } = await nodeAPI.readDetail(
          node.originalNodeObject.unified_job_template
        );
        updatedNode.fullUnifiedJobTemplate = fullUnifiedJobTemplate;
      } catch (err) {
        setDetailError(err);
        return null;
      }
    }

    if (
      node?.originalNodeObject?.summary_fields?.unified_job_template
        ?.unified_job_type === 'job' &&
      !node?.originalNodeCredentials
    ) {
      try {
        const {
          data: { results },
        } = await WorkflowJobTemplateNodesAPI.readCredentials(
          node.originalNodeObject.id
        );
        updatedNode.originalNodeCredentials = results;
      } catch (err) {
        setCredentialsError(err);
        return null;
      }
    }

    dispatch({
      type: 'SET_NODES',
      value: updatedNodes,
    });

    return updatedNode;
  };

  const handleEditClick = async () => {
    updateHelpText(null);
    setHovering(false);
    const nodeToEdit = await updateNode();

    if (nodeToEdit) {
      dispatch({ type: 'SET_NODE_TO_EDIT', value: nodeToEdit });
    }
  };

  const handleViewClick = async () => {
    updateHelpText(null);
    setHovering(false);
    const nodeToView = await updateNode();

    if (nodeToView) {
      dispatch({ type: 'SET_NODE_TO_VIEW', value: nodeToView });
    }
  };

  const handleNodeMouseEnter = () => {
    ref.current.parentNode.appendChild(ref.current);
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
      dispatch({ type: 'SET_ADD_LINK_TARGET_NODE', value: node });
    }
  };

  const viewDetailsAction = (
    <WorkflowActionTooltipItem
      id="node-details"
      key="details"
      onClick={handleViewClick}
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
            dispatch({ type: 'START_ADD_NODE', sourceNodeId: node.id });
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
          onClick={handleEditClick}
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
            dispatch({ type: 'SELECT_SOURCE_FOR_LINKING', node });
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
            dispatch({ type: 'SET_NODE_TO_DELETE', value: node });
          }}
          onMouseEnter={() => updateHelpText(i18n._(t`Delete this node`))}
          onMouseLeave={() => updateHelpText(null)}
        >
          <TrashAltIcon />
        </WorkflowActionTooltipItem>,
      ];

  return (
    <>
      <NodeG
        id={`node-${node.id}`}
        job={node.job}
        noPointerEvents={isAddLinkSourceNode}
        onMouseEnter={handleNodeMouseEnter}
        onMouseLeave={handleNodeMouseLeave}
        ref={ref}
        transform={`translate(${nodePositions[node.id].x},${nodePositions[
          node.id
        ].y - nodePositions[1].y})`}
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
          strokeWidth="2px"
          width={wfConstants.nodeW}
        />
        <foreignObject
          height="58"
          {...(!addingLink && {
            onMouseEnter: () => updateNodeHelp(node),
            onMouseLeave: () => updateNodeHelp(null),
          })}
          onClick={() => handleNodeClick()}
          width="178"
          x="1"
          y="1"
        >
          <NodeContents isInvalidLinkTarget={node.isInvalidLinkTarget}>
            <NodeResourceName id={`node-${node.id}-name`}>
              {node?.fullUnifiedJobTemplate?.name ||
                node?.originalNodeObject?.summary_fields?.unified_job_template
                  ?.name ||
                i18n._(t`DELETED`)}
            </NodeResourceName>
          </NodeContents>
        </foreignObject>
        <WorkflowNodeTypeLetter node={node} />
        {hovering && !addingLink && (
          <WorkflowActionTooltip
            pointX={wfConstants.nodeW}
            pointY={wfConstants.nodeH / 2}
            actions={tooltipActions}
          />
        )}
      </NodeG>
      {detailError && (
        <AlertModal
          isOpen={detailError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={handleDetailErrorClose}
        >
          {i18n._(t`Failed to retrieve full node resource object.`)}
          <ErrorDetail error={detailError} />
        </AlertModal>
      )}
      {credentialsError && (
        <AlertModal
          isOpen={credentialsError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={handleCredentialsErrorClose}
        >
          {i18n._(t`Failed to retrieve node credentials.`)}
          <ErrorDetail error={credentialsError} />
        </AlertModal>
      )}
    </>
  );
}

VisualizerNode.propTypes = {
  node: shape().isRequired,
  onMouseOver: func,
  readOnly: bool.isRequired,
  updateHelpText: func.isRequired,
  updateNodeHelp: func.isRequired,
};

VisualizerNode.defaultProps = {
  onMouseOver: () => {},
};

export default withI18n()(VisualizerNode);
