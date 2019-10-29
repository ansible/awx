import DataListCell from '@components/DataListCell';
import styled from 'styled-components';

const ActionButtonCell = styled(DataListCell)`
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;
ActionButtonCell.displayName = 'ActionButtonCell';
export default ActionButtonCell;
