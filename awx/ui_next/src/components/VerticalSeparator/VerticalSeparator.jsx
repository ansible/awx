import React from 'react';
import styled from 'styled-components';

const Separator = styled.span`
  display: inline-block;
  width: 1px;
  height: 30px;
  margin-right: 20px;
  margin-left: 20px;
  background-color: #d7d7d7;
  vertical-align: middle;
`;

const VerticalSeparator = () => (
  <div>
    <Separator />
  </div>
);

export default VerticalSeparator;
