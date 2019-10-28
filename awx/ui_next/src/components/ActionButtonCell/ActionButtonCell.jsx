import DataListCell from '@components/DataListCell';
import styled from 'styled-components';

DataListCell.displayName = 'ActionButtonCell';
export default styled(DataListCell)`
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;
