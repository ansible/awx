import styled from 'styled-components';
import { CardHeader } from '@patternfly/react-core';

const TabbedCardHeader = styled(CardHeader)`
  --pf-c-card--first-child--PaddingTop: 0;
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
  position: relative;
`;

export default TabbedCardHeader;
