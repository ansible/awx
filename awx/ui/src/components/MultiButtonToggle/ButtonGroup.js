import React from 'react';
import styled from 'styled-components';

const Group = styled.div`
  display: inline-flex;

  & > .pf-c-button:not(:last-child) {
    &,
    &::after {
      border-top-right-radius: 0;
      border-bottom-right-radius: 0;
    }
  }

  & > .pf-c-button:not(:first-child) {
    &,
    &::after {
      border-top-left-radius: 0;
      border-bottom-left-radius: 0;
    }
  }
`;

function ButtonGroup({ children }) {
  return <Group>{children}</Group>;
}

export default ButtonGroup;
