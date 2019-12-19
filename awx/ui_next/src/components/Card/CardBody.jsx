import styled from 'styled-components';
import { CardBody } from '@patternfly/react-core';

const TabbedCardBody = styled(CardBody)`
  padding-top: var(--pf-c-card--first-child--PaddingTop);
`;
CardBody.displayName = 'PFCardBody';

export default TabbedCardBody;
