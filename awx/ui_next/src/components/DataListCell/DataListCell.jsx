import { DataListCell as PFDataListCell } from '@patternfly/react-core';
import styled from 'styled-components';

PFDataListCell.displayName = 'PFDataListCell';
// Once https://github.com/patternfly/patternfly-react/issues/3938
// has been resolved this component can be removed
const DataListCell = styled(PFDataListCell)`
  word-break: break-word;
`;
DataListCell.displayName = 'DataListCell';

export default DataListCell;
