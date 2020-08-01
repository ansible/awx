import React, { useContext, useEffect, useRef, useState } from 'react';
import { func, shape } from 'prop-types';
import { WorkflowStateContext } from '../../../contexts/Workflow';
import {
  generateLine,
  getLinePoints,
  getLinkOverlayPoints,
} from '../../../components/Workflow/WorkflowUtils';

function WorkflowOutputLink({ link, mouseEnter, mouseLeave }) {
  const ref = useRef(null);
  const [hovering, setHovering] = useState(false);
  const [pathD, setPathD] = useState();
  const [pathStroke, setPathStroke] = useState('#CCCCCC');
  const { nodePositions } = useContext(WorkflowStateContext);

  const handleLinkMouseEnter = () => {
    ref.current.parentNode.appendChild(ref.current);
    setHovering(true);
    mouseEnter();
  };

  const handleLinkMouseLeave = () => {
    ref.current.parentNode.prepend(ref.current);
    setHovering(null);
    mouseLeave();
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
      ref={ref}
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
        onMouseEnter={() => mouseEnter()}
        onMouseLeave={() => mouseLeave()}
        opacity="0"
        points={getLinkOverlayPoints(link, nodePositions)}
      />
    </g>
  );
}

WorkflowOutputLink.propTypes = {
  link: shape().isRequired,
  mouseEnter: func.isRequired,
  mouseLeave: func.isRequired,
};

export default WorkflowOutputLink;
