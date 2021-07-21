import React, { Fragment } from 'react';

import { BackgroundImage } from '@patternfly/react-core';

export default ({ children }) => (
  <>
    <BackgroundImage />
    {children}
  </>
);
