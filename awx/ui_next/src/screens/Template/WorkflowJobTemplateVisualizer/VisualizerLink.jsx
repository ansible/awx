import React, { useEffect, useRef, useState } from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { bool, func, shape } from 'prop-types';
import { PencilAltIcon, PlusIcon, TrashAltIcon } from '@patternfly/react-icons';
import {
  generateLine,
  getLinePoints,
  getLinkOverlayPoints,
} from '@components/Workflow/WorkflowUtils';
import {
  WorkflowActionTooltip,
  WorkflowActionTooltipItem,
} from '@components/Workflow';

const LinkG = styled.g`
  pointer-events: ${props => (props.ignorePointerEvents ? 'none' : 'auto')};
`;

function VisualizerLink({
  addingLink,
  i18n,
  link,
  nodePositions,
  onAddNodeClick,
  onDeleteLinkClick,
  onLinkEditClick,
  onUpdateHelpText,
  onUpdateLinkHelp,
  readOnly,
}) {
  const ref = useRef(null);
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
        onUpdateHelpText(null);
        setHovering(false);
        onAddNodeClick(link.source.id, link.target.id);
      }}
      onMouseEnter={() =>
        onUpdateHelpText(i18n._(t`Add a new node between these two nodes`))
      }
      onMouseLeave={() => onUpdateHelpText(null)}
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
            onClick={() => onLinkEditClick(link)}
            onMouseEnter={() => onUpdateHelpText(i18n._(t`Edit this link`))}
            onMouseLeave={() => onUpdateHelpText(null)}
          >
            <PencilAltIcon />
          </WorkflowActionTooltipItem>,
          <WorkflowActionTooltipItem
            id="link-delete"
            key="delete"
            onClick={() => onDeleteLinkClick(link)}
            onMouseEnter={() => onUpdateHelpText(i18n._(t`Delete this link`))}
            onMouseLeave={() => onUpdateHelpText(null)}
          >
            <TrashAltIcon />
          </WorkflowActionTooltipItem>,
        ];

  const handleLinkMouseEnter = () => {
    ref.current.parentNode.appendChild(ref.current);
    setHovering(true);
  };

  const handleLinkMouseLeave = () => {
    ref.current.parentNode.prepend(ref.current);
    setHovering(null);
  };

  useEffect(() => {
    if (link.linkType === 'failure') {
      setPathStroke('#d9534f');
    }
    if (link.linkType === 'success') {
      setPathStroke('#5cb85c');
    }
    if (link.linkType === 'always') {
      setPathStroke('#337ab7');
    }
  }, [link.linkType]);

  useEffect(() => {
    const linePoints = getLinePoints(link, nodePositions);
    setPathD(generateLine(linePoints));
    setTooltipX((linePoints[0].x + linePoints[1].x) / 2);
    setTooltipY((linePoints[0].y + linePoints[1].y) / 2);
  }, [link, nodePositions]);

  return (
    <LinkG
      id={`link-${link.source.id}-${link.target.id}`}
      ignorePointerEvents={addingLink}
      onMouseEnter={handleLinkMouseEnter}
      onMouseLeave={handleLinkMouseLeave}
      ref={ref}
    >
      <polygon
        fill="#E1E1E1"
        id={`link-${link.source.id}-${link.target.id}-overlay`}
        opacity={hovering ? '1' : '0'}
        points={getLinkOverlayPoints(link, nodePositions)}
      />
      <path d={pathD} stroke={pathStroke} strokeWidth="2px" />
      <polygon
        onMouseEnter={() => onUpdateLinkHelp(link)}
        onMouseLeave={() => onUpdateLinkHelp(null)}
        opacity="0"
        points={getLinkOverlayPoints(link, nodePositions)}
      />
      {!readOnly && hovering && (
        <WorkflowActionTooltip
          actions={tooltipActions}
          pointX={tooltipX}
          pointY={tooltipY}
        />
      )}
    </LinkG>
  );
}

VisualizerLink.propTypes = {
  addingLink: bool.isRequired,
  link: shape().isRequired,
  nodePositions: shape().isRequired,
  onAddNodeClick: func.isRequired,
  onDeleteLinkClick: func.isRequired,
  onLinkEditClick: func.isRequired,
  readOnly: bool.isRequired,
  onUpdateHelpText: func.isRequired,
  onUpdateLinkHelp: func.isRequired,
};

export default withI18n()(VisualizerLink);
