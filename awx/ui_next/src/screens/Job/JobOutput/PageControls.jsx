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
  display: flex;
  height: 35px;
  outline: 1px solid #d7d7d7;
  width: 100%;
`;

const Button = styled(PFButton)`
  position: relative;
  z-index: 1;
`;

const PageControls = ({
  onScrollFirst,
  onScrollLast,
  onScrollNext,
  onScrollPrevious,
}) => (
  <Wrapper>
    <Button variant="plain" css="margin-right: auto">
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

export default PageControls;
