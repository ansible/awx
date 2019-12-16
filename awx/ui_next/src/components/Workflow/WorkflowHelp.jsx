import React from 'react';
import styled from 'styled-components';

const Outer = styled.div`
  position: relative;
  height: 0;
  pointer-events: none;
`;

const Inner = styled.div`
  position: absolute;
  left: 10px;
  top: 10px;
  background-color: #383f44;
  color: white;
  padding: 5px 10px;
  border-radius: 2px;
  max-width: 300px;
`;

function WorkflowHelp({ children }) {
  return (
    <Outer>
      <Inner>{children}</Inner>
    </Outer>
  );
}

export default WorkflowHelp;
