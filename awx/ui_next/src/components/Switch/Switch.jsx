import { Switch } from '@patternfly/react-core';
import styled from 'styled-components';

Switch.displayName = 'PFSwitch';
export default styled(Switch)`
  display: flex;
  flex-wrap: no-wrap;
  /* workaround PF bug; used in calculating switch width: */
  --pf-c-switch__toggle-icon--Offset: 0.125rem;
`;
