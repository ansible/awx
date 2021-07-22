import React from 'react';
import styled from 'styled-components';
import { node, number } from 'prop-types';

const TooltipContents = styled.div`
  display: flex;
`;

const TooltipArrow = styled.div`
  width: 10px;
`;

const TooltipArrowOuter = styled.div`
  border-bottom: 10px solid transparent;
  border-right: 10px solid #c4c4c4;
  border-top: 10px solid transparent;
  height: 0;
  margin: auto;
  position: absolute;
  top: calc(50% - 10px);
  width: 0;
`;

const TooltipArrowInner = styled.div`
  border-bottom: 10px solid transparent;
  border-right: 10px solid white;
  border-top: 10px solid transparent;
  height: 0;
  left: 2px;
  margin: auto;
  position: absolute;
  top: calc(50% - 10px);
  width: 0;
`;

const TooltipActions = styled.div`
  background-color: white;
  border-radius: 2px;
  border: 1px solid #c4c4c4;
  padding: 5px;
`;

function WorkflowActionTooltip({ actions, pointX, pointY }) {
  const tipHeight = 25 * actions.length + 5 * actions.length - 1 + 10;
  return (
    <foreignObject
      x={pointX}
      y={Number(pointY) - tipHeight / 2}
      width="52"
      height={tipHeight}
    >
      <TooltipContents>
        <TooltipArrow>
          <TooltipArrowOuter />
          <TooltipArrowInner />
        </TooltipArrow>
        <TooltipActions>{actions}</TooltipActions>
      </TooltipContents>
    </foreignObject>
  );
}

WorkflowActionTooltip.propTypes = {
  actions: node.isRequired,
  pointX: number.isRequired,
  pointY: number.isRequired,
};

export default WorkflowActionTooltip;
