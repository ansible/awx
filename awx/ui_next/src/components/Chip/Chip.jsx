import { Chip } from '@patternfly/react-core';
import styled from 'styled-components';

Chip.displayName = 'PFChip';
export default styled(Chip)`
  --pf-c-chip--m-read-only--PaddingTop: 3px;
  --pf-c-chip--m-read-only--PaddingBottom: 3px;
  --pf-c-chip--m-read-only--PaddingLeft: 8px;
  --pf-c-chip--m-read-only--PaddingRight: 8px;

  .pf-c-button {
    --pf-c-button--PaddingTop: 3px;
    --pf-c-button--PaddingBottom: 3px;
    --pf-c-button--PaddingLeft: 8px;
    --pf-c-button--PaddingRight: 8px;
  }
`;
