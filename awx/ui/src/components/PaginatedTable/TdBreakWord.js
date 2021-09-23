import React from 'react';
import { Td as _Td } from '@patternfly/react-table';
import styled from 'styled-components';

const Td = styled(_Td)`
  && {
    word-break: break-all;
  }
`;

export default function TdBreakWord({ children, ...props }) {
  return <Td {...props}>{children}</Td>;
}
