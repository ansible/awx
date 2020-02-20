import React from 'react';
import styled from 'styled-components';
import { func } from 'prop-types';

const TooltipItem = styled.div`
  align-items: center;
  border-radius: 2px;
  cursor: pointer;
  display: flex;
  font-size: 12px;
  height: 25px;
  justify-content: center;
  width: 25px;

  &:hover {
    color: white;
    background-color: #c4c4c4;
  }

  &:not(:last-of-type) {
    margin-bottom: 5px;
  }
`;

function WorkflowActionTooltipItem({
  children,
  onClick,
  onMouseEnter,
  onMouseLeave,
  ...rest
}) {
  return (
    <TooltipItem
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      {...rest}
    >
      {children}
    </TooltipItem>
  );
}

WorkflowActionTooltipItem.propTypes = {
  onClick: func,
  onMouseEnter: func,
  onMouseLeave: func,
};

WorkflowActionTooltipItem.defaultProps = {
  onClick: () => {},
  onMouseEnter: () => {},
  onMouseLeave: () => {},
};

export default WorkflowActionTooltipItem;
