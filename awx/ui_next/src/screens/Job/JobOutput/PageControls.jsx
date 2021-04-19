import 'styled-components/macro';
import React from 'react';

import { t } from '@lingui/macro';
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
    <Button
      ouiaId="job-output-expand-collapse-lines-button"
      aria-label={t`Toggle expand/collapse event lines`}
      variant="plain"
      css="margin-right: auto"
    >
      <PlusIcon />
    </Button>
    <Button
      ouiaId="job-output-scroll-previous-button"
      aria-label={t`Scroll previous`}
      onClick={onScrollPrevious}
      variant="plain"
    >
      <AngleUpIcon />
    </Button>
    <Button
      ouiaId="job-output-scroll-next-button"
      aria-label={t`Scroll next`}
      onClick={onScrollNext}
      variant="plain"
    >
      <AngleDownIcon />
    </Button>
    <Button
      ouiaId="job-output-scroll-first-button"
      aria-label={t`Scroll first`}
      onClick={onScrollFirst}
      variant="plain"
    >
      <AngleDoubleUpIcon />
    </Button>
    <Button
      ouiaId="job-output-scroll-last-button"
      aria-label={t`Scroll last`}
      onClick={onScrollLast}
      variant="plain"
    >
      <AngleDoubleDownIcon />
    </Button>
  </Wrapper>
);

export default PageControls;
