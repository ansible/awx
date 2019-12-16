import React from 'react';
import styled from 'styled-components';

const TooltipContents = styled.div`
  display: flex;
`;

const TooltipArrows = styled.div`
  width: 10px;
`;

const TooltipArrowOuter = styled.div`
  position: absolute;
  top: calc(50% - 10px);
  width: 0;
  height: 0;
  border-right: 10px solid #c4c4c4;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  margin: auto;
`;

const TooltipArrowInner = styled.div`
  position: absolute;
  top: calc(50% - 10px);
  left: 2px;
  width: 0;
  height: 0;
  border-right: 10px solid white;
  border-top: 10px solid transparent;
  border-bottom: 10px solid transparent;
  margin: auto;
`;

const TooltipActions = styled.div`
  background-color: white;
  border: 1px solid #c4c4c4;
  border-radius: 2px;
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
        <TooltipArrows>
          <TooltipArrowOuter />
          <TooltipArrowInner />
        </TooltipArrows>
        <TooltipActions>{actions}</TooltipActions>
      </TooltipContents>
    </foreignObject>
  );
}

export default WorkflowActionTooltip;
