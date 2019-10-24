import DataListCell from '@components/DataListCell';
import styled from 'styled-components';

export default styled(DataListCell)`
  & > :not(:first-child) {
    margin-left: 20px;
  }
`;
