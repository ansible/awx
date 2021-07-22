import React from 'react';
import styled from 'styled-components';

const Outer = styled.div`
  height: 0;
  pointer-events: none;
  position: relative;
`;

const Inner = styled.div`
  background-color: #383f44;
  border-radius: 2px;
  color: white;
  left: 10px;
  max-width: 300px;
  padding: 5px 10px;
  position: absolute;
  top: 10px;
`;

function WorkflowHelp({ children }) {
  return (
    <Outer>
      <Inner>{children}</Inner>
    </Outer>
  );
}

export default WorkflowHelp;
