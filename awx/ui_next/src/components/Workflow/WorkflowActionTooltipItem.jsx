import React from 'react';
import styled from 'styled-components';

const TooltipItem = styled.div`
  height: 25px;
  width: 25px;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 2px;

  &:hover {
    color: white;
    background-color: #c4c4c4;
  }

  &:not(:last-of-type) {
    margin-bottom: 5px;
  }
`;

function WorkflowActionTooltip({
  children,
  onMouseEnter,
  onMouseLeave,
  onClick,
}) {
  return (
    <TooltipItem
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
    >
      {children}
    </TooltipItem>
  );
}

export default WorkflowActionTooltip;
