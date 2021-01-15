import React from 'react';

import { Spinner } from '@patternfly/react-core';
import styled from 'styled-components';

const UpdatingContent = styled.div`
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 300;
  width: 100%;
  height: 100%;
  & + * {
    opacity: 0.5;
  }
`;

const LoadingSpinner = () => (
  <UpdatingContent>
    <Spinner />
  </UpdatingContent>
);
export default LoadingSpinner;
