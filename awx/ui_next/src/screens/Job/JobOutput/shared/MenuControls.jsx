import React, { Component } from 'react';
import { Button as PFButton } from '@patternfly/react-core';
import {
  PlusIcon,
  AngleDoubleUpIcon,
  AngleDoubleDownIcon,
  AngleUpIcon,
  AngleDownIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';

const Wrapper = styled.div`
  display: grid;
  grid-gap: 20px;
  grid-template-columns: repeat(5, 1fr);
`;

const Button = styled(PFButton)`
  &:hover {
    background-color: #0066cc;
    color: white;
  }
`;

class MenuControls extends Component {
  render() {
    return (
      <Wrapper>
        <Button
          variant="plain"
        >
          <PlusIcon />
        </Button>
        <Button
          variant="plain"
        >
          <AngleUpIcon />
        </Button>
        <Button
          variant="plain"
        >
          <AngleDownIcon />
        </Button>
        <Button
          variant="plain"
        >
          <AngleDoubleUpIcon />
        </Button>
        <Button
          variant="plain"
        >
          <AngleDoubleDownIcon />
        </Button>
      </Wrapper>
    );
  }
}

export default MenuControls;
