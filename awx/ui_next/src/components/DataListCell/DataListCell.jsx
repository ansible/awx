import { DataListCell as PFDataListCell } from '@patternfly/react-core';
import styled from 'styled-components';

const DataListCell = styled(PFDataListCell)`
  display: flex;
  align-items: center;
  padding-bottom: ${props => (props.righthalf ? '16px' : '8px')};
  @media screen and (min-width: 768px) {
    padding-bottom: 0;
    justify-content: ${props => (props.lastcolumn ? 'flex-end' : 'inherit')};
  }
`;

export default DataListCell;
