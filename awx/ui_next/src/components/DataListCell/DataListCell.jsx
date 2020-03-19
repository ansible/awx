import { DataListCell } from '@patternfly/react-core';
import styled from 'styled-components';

DataListCell.displayName = 'PFDataListCell';
// Once https://github.com/patternfly/patternfly-react/issues/3938
// has been resolved this component can be removed
export default styled(DataListCell)`
  word-break: break-word;
`;
