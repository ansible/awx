import React, { useEffect, useState } from 'react';
import { shape } from 'prop-types';
import { generateLine, getLinePoints } from '@util/workflow';

function WorkflowOutputLink({ link, nodePositions }) {
  const [pathD, setPathD] = useState();
  const [pathStroke, setPathStroke] = useState('#CCCCCC');

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
      className="WorkflowGraph-link"
      id={`link-${link.source.id}-${link.target.id}`}
    >
      <path
        className="WorkflowGraph-linkPath"
        d={pathD}
        stroke={pathStroke}
        strokeWidth="2px"
      />
    </g>
  );
}

WorkflowOutputLink.propTypes = {
  link: shape().isRequired,
  nodePositions: shape().isRequired,
};

export default WorkflowOutputLink;
