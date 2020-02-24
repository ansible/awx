import styled from 'styled-components';
import { CardHeader } from '@patternfly/react-core';

const TabbedCardHeader = styled(CardHeader)`
  --pf-c-card--first-child--PaddingTop: 0;
  --pf-c-card--child--PaddingLeft: 0;
  --pf-c-card--child--PaddingRight: 0;
  --pf-c-card__header--not-last-child--PaddingBottom: 24px;
  --pf-c-card__header--not-last-child--PaddingBottom: 0;
  display: flex;
`;

export default TabbedCardHeader;
