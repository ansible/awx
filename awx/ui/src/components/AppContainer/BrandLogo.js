import React from 'react';

import styled from 'styled-components';

const BrandImg = styled.img`
  flex: initial;
  height: 76px;
  width: initial;
  padding-left: 0px;
  margin: 0px 0px 0px 0px;
  max-width: 100px;
  max-height: initial;
  pointer-events: none;
`;

const BrandLogo = ({ alt }) => (
  <BrandImg src="static/media/logo-header.svg" alt={alt} />
);

export default BrandLogo;
