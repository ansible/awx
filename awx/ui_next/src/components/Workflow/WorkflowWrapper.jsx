import React from 'react';
import styled from 'styled-components';

const WorkflowWrapperDiv = styled.div`
  display: flex;
  flex-flow: column;
  height: 100%;

  svg {
    display: flex;
    height: 100%;
    background-color: #f6f6f6;
  }

  @keyframes pulse {
    from {
      -webkit-transform: scale(1);
    }
    to {
      -webkit-transform: scale(0);
    }
  }

  .WorkflowGraph-nodeContents {
    font-size: 13px;
    padding: 0px 10px;
  }

  .WorkflowGraph-nameText {
    margin-top: 20px;
    text-align: center;
  }

  .WorkflowGraph-ellipsisText {
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .WorkflowGraph-jobTopLine {
    display: flex;
    align-items: center;
    margin-top: 5px;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }

  .WorkflowGraph-jobStatus {
    height: 15px;
    width: 15px;
    margin-right: 10px;
  }

  .WorkflowGraph-jobStatus--waiting {
    border: 1px solid #d7d7d7;
  }

  .WorkflowGraph-jobStatus--running {
    background-color: #5cb85c;
    text-shadow: -1px -1px 0 #ffffff, 1px -1px 0 #ffffff, -1px 1px 0 #ffffff,
      1px 1px 0 #ffffff;
    animation: pulse 1.5s linear infinite alternate;
  }

  .WorkflowGraph-jobStatus--fail {
    background-color: #d9534f;
  }

  .WorkflowGraph-jobStatus--success {
    background-color: #5cb85c;
  }

  .WorkflowGraph-jobStatus--split {
    flex: 0 1 auto;
    > * {
      width: 100%;
      height: 50%;
    }
  }

  .WorkflowGraph-jobStatus--whiteTop {
    border: 1px solid #b7b7b7;
    border-bottom: 0;
    background-color: #ffffff;
  }

  .WorkflowGraph-jobStatus--whiteBottom {
    border: 1px solid #b7b7b7;
    border-top: 0;
    background-color: #ffffff;
  }

  .WorkflowGraph-elapsedWrapper {
    text-align: center;
    margin-top: 5px;
  }

  .WorkflowGraph-elapsedText {
    font-size: 12px;
    font-weight: bold;
    background-color: #ededed;
    padding: 3px 12px;
    border-radius: 14px;
  }

  .WorkflowGraph-tooltip {
    padding-left: 5px;
  }

  .WorkflowGraph-action {
    height: 25px;
    width: 25px;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 2px;
  }

  .WorkflowGraph-action:hover {
    color: white;
  }

  .WorkflowGraph-action:not(:last-of-type) {
    margin-bottom: 5px;
  }

  .WorkflowGraph-action--add:hover {
    background-color: #58b957;
  }

  .WorkflowGraph-action--edit:hover,
  .WorkflowGraph-action--link:hover,
  .WorkflowGraph-action--details:hover {
    background-color: #0279bc;
  }

  .WorkflowGraph-action--delete:hover {
    background-color: #d9534f;
  }

  .WorkflowGraph-tooltipArrows {
    width: 10px;
  }

  .WorkflowGraph-tooltipArrows--outer {
    position: absolute;
    top: calc(50% - 10px);
    width: 0;
    height: 0;
    border-right: 10px solid #c4c4c4;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    margin: auto;
  }

  .WorkflowGraph-tooltipArrows--inner {
    position: absolute;
    top: calc(50% - 10px);
    left: 6px;
    width: 0;
    height: 0;
    border-right: 10px solid white;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    margin: auto;
  }

  .WorkflowGraph-tooltipActions {
    background-color: white;
    border: 1px solid #c4c4c4;
    border-radius: 2px;
    padding: 5px;
  }

  .WorkflowGraph-tooltipContents {
    display: flex;
  }
`;

function WorkflowWrapper({ children }) {
  return <WorkflowWrapperDiv>{children}</WorkflowWrapperDiv>;
}

export default WorkflowWrapper;
