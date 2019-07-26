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
  onScrollTop,
  onScrollBottom,
  onScrollNext,
  onScrollPrevious,
}) => (
  <Wrapper>
    <Button variant="plain">
      <PlusIcon />
    </Button>
    <Button onClick={onScrollPrevious} variant="plain">
      <AngleUpIcon />
    </Button>
    <Button onClick={onScrollNext} variant="plain">
      <AngleDownIcon />
    </Button>
    <Button onClick={onScrollTop} variant="plain">
      <AngleDoubleUpIcon />
    </Button>
    <Button onClick={onScrollBottom} variant="plain">
      <AngleDoubleDownIcon />
    </Button>
  </Wrapper>
);

export default MenuControls;
