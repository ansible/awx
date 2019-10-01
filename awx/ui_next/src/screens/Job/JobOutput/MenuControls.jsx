import React from 'react';
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

const MenuControls = ({
  onScrollFirst,
  onScrollLast,
  onScrollNext,
  onScrollPrevious,
}) => (
  <Wrapper>
    <Button variant="plain">
      <PlusIcon />
    </Button>
    <Button
      aria-label="scroll previous"
      onClick={onScrollPrevious}
      variant="plain"
    >
      <AngleUpIcon />
    </Button>
    <Button aria-label="scroll next" onClick={onScrollNext} variant="plain">
      <AngleDownIcon />
    </Button>
    <Button aria-label="scroll first" onClick={onScrollFirst} variant="plain">
      <AngleDoubleUpIcon />
    </Button>
    <Button aria-label="scroll last" onClick={onScrollLast} variant="plain">
      <AngleDoubleDownIcon />
    </Button>
  </Wrapper>
);

export default MenuControls;
