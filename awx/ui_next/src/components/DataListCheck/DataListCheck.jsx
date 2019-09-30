import { DataListCheck as PFDataListCheck } from '@patternfly/react-core';
import styled from 'styled-components';

export default styled(PFDataListCheck)`
  padding-top: 18px;
  @media screen and (min-width: 768px) {
    padding-top: 16px;
    justify-content: ${props => (props.lastcolumn ? 'flex-end' : 'inherit')};
    .pf-c-data-list__check {
      display: flex;
      align-items: center;
    }
  }
`;
