import { ChipGroup } from '@patternfly/react-core';
import styled from 'styled-components';

export default styled(ChipGroup)`
  --pf-c-chip-group--c-chip--MarginRight: 10px;
  --pf-c-chip-group--c-chip--MarginBottom: 10px;

  > .pf-c-chip.pf-m-overflow .pf-c-button {
    --pf-c-button--PaddingTop: 3px;
    --pf-c-button--PaddingBottom: 3px;
    --pf-c-chip--m-overflow--c-button--PaddingLeft: 8px;
    --pf-c-chip--m-overflow--c-button--PaddingRight: 8px;
  }
`;
