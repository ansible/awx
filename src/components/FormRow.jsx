import React from 'react';
import styled from 'styled-components';

export default function FormRow ({ children }) {
  const Row = styled.div`
  display: grid;
  grid-gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  `;
  return (
    <Row>
      {children}
    </Row>
  );
}
