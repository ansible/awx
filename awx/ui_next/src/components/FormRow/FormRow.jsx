import React from 'react';
import styled from 'styled-components';

const Row = styled.div`
  display: grid;
  grid-gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
`;
export default function FormRow({ children }) {
  return <Row>{children}</Row>;
}
