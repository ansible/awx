import React, { useEffect, useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PencilAltIcon, PlusIcon, TrashAltIcon } from '@patternfly/react-icons';
import {
  generateLine,
  getLinkOverlayPoints,
  getLinePoints,
} from '@util/workflow';
import {
  WorkflowActionTooltip,
  WorkflowActionTooltipItem,
} from '@components/Workflow';

const LinkG = styled.g`
  pointer-events: ${props => (props.ignorePointerEvents ? 'none' : 'auto')};
`;

function VisualizerLink({
  link,
  nodePositions,
  readOnly,
  updateHelpText,
  updateLinkHelp,
  i18n,
  onLinkEditClick,
  onDeleteLinkClick,
  addingLink,
  onAddNodeClick,
}) {
  const [hovering, setHovering] = useState(false);
  const [pathD, setPathD] = useState();
  const [pathStroke, setPathStroke] = useState('#CCCCCC');
  const [tooltipX, setTooltipX] = useState();
  const [tooltipY, setTooltipY] = useState();

  const addNodeAction = (
    <WorkflowActionTooltipItem
      id="link-add-node"
      key="add"
      onClick={() => {
        updateHelpText(null);
        setHovering(false);
        onAddNodeClick(link.source.id, link.target.id);
      }}
      onMouseEnter={() =>
        updateHelpText(i18n._(t`Add a new node between these two nodes`))
      }
      onMouseLeave={() => updateHelpText(null)}
    >
      <PlusIcon />
    </WorkflowActionTooltipItem>
  );

  const tooltipActions =
    link.source.id === 1
      ? [addNodeAction]
      : [
          addNodeAction,
          <WorkflowActionTooltipItem
            id="link-edit"
            key="edit"
            onMouseEnter={() => updateHelpText(i18n._(t`Edit this link`))}
            onMouseLeave={() => updateHelpText(null)}
            onClick={() => onLinkEditClick(link)}
          >
            <PencilAltIcon />
          </WorkflowActionTooltipItem>,
          <WorkflowActionTooltipItem
            id="link-delete"
            key="delete"
            onMouseEnter={() => updateHelpText(i18n._(t`Delete this link`))}
            onMouseLeave={() => updateHelpText(null)}
            onClick={() => onDeleteLinkClick(link)}
          >
            <TrashAltIcon />
          </WorkflowActionTooltipItem>,
        ];

  const handleLinkMouseEnter = () => {
    const linkEl = document.getElementById(
      `link-${link.source.id}-${link.target.id}`
    );
    linkEl.parentNode.appendChild(linkEl);
    setHovering(true);
  };

  const handleLinkMouseLeave = () => {
    const linkEl = document.getElementById(
      `link-${link.source.id}-${link.target.id}`
    );
    linkEl.parentNode.prepend(linkEl);
    setHovering(null);
  };

  useEffect(() => {
    if (link.edgeType === 'failure') {
      setPathStroke('#d9534f');
    }
    if (link.edgeType === 'success') {
      setPathStroke('#5cb85c');
    }
    if (link.edgeType === 'always') {
      setPathStroke('#337ab7');
    }
  }, [link.edgeType]);

  useEffect(() => {
    const linePoints = getLinePoints(link, nodePositions);
    setPathD(generateLine(linePoints));
    setTooltipX((linePoints[0].x + linePoints[1].x) / 2);
    setTooltipY((linePoints[0].y + linePoints[1].y) / 2);
  }, [link, nodePositions]);

  return (
    <LinkG
      className="WorkflowGraph-link"
      id={`link-${link.source.id}-${link.target.id}`}
      onMouseEnter={handleLinkMouseEnter}
      onMouseLeave={handleLinkMouseLeave}
      ignorePointerEvents={addingLink}
    >
      <polygon
        id={`link-${link.source.id}-${link.target.id}-overlay`}
        fill="#E1E1E1"
        opacity={hovering ? '1' : '0'}
        points={getLinkOverlayPoints(link, nodePositions)}
      />
      <path
        className="WorkflowGraph-linkPath"
        d={pathD}
        stroke={pathStroke}
        strokeWidth="2px"
      />
      <polygon
        opacity="0"
        points={getLinkOverlayPoints(link, nodePositions)}
        onMouseEnter={() => updateLinkHelp(link)}
        onMouseLeave={() => updateLinkHelp(null)}
      />
      {!readOnly && hovering && (
        <WorkflowActionTooltip
          pointX={tooltipX}
          pointY={tooltipY}
          actions={tooltipActions}
        />
      )}
    </LinkG>
  );
}

export default withI18n()(VisualizerLink);
