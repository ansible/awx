import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
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
  i18n,
  onScrollFirst,
  onScrollLast,
  onScrollNext,
  onScrollPrevious,
}) => (
  <Wrapper>
    <Button
      aria-label={i18n._(t`Toggle expand/collapse event lines`)}
      variant="plain"
      css="margin-right: auto"
    >
      <PlusIcon />
    </Button>
    <Button
      aria-label={i18n._(t`Scroll previous`)}
      onClick={onScrollPrevious}
      variant="plain"
    >
      <AngleUpIcon />
    </Button>
    <Button
      aria-label={i18n._(t`Scroll next`)}
      onClick={onScrollNext}
      variant="plain"
    >
      <AngleDownIcon />
    </Button>
    <Button
      aria-label={i18n._(t`Scroll first`)}
      onClick={onScrollFirst}
      variant="plain"
    >
      <AngleDoubleUpIcon />
    </Button>
    <Button
      aria-label={i18n._(t`Scroll last`)}
      onClick={onScrollLast}
      variant="plain"
    >
      <AngleDoubleDownIcon />
    </Button>
  </Wrapper>
);

export default withI18n()(PageControls);
