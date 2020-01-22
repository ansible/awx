import React, { useEffect, useState } from 'react';
import { shape } from 'prop-types';
import {
  generateLine,
  getLinePoints,
  getLinkOverlayPoints,
} from '@util/workflow';

function WorkflowOutputLink({ link, nodePositions, onUpdateLinkHelp }) {
  const [hovering, setHovering] = useState(false);
  const [pathD, setPathD] = useState();
  const [pathStroke, setPathStroke] = useState('#CCCCCC');

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
  }, [link, nodePositions]);

  return (
    <g
      id={`link-${link.source.id}-${link.target.id}`}
      onMouseEnter={handleLinkMouseEnter}
      onMouseLeave={handleLinkMouseLeave}
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
    </g>
  );
}

WorkflowOutputLink.propTypes = {
  link: shape().isRequired,
  nodePositions: shape().isRequired,
};

export default WorkflowOutputLink;
