import React, { Fragment } from 'react';

import { BackgroundImage } from '@patternfly/react-core';

export default ({ children }) => (
  <Fragment>
    <BackgroundImage />
    {children}
  </Fragment>
);
