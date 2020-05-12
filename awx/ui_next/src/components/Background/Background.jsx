import React, { Fragment } from 'react';

import { BackgroundImage, BackgroundImageSrc } from '@patternfly/react-core';

const backgroundImageConfig = {
  [BackgroundImageSrc.xs]: './images/pfbg_576.jpg',
  [BackgroundImageSrc.xs2x]: './images/pfbg_576@2x.jpg',
  [BackgroundImageSrc.sm]: './images/pfbg_768.jpg',
  [BackgroundImageSrc.sm2x]: './images/pfbg_768@2x.jpg',
  [BackgroundImageSrc.lg]: './images/pfbg_2000.jpg',
};

export default ({ children }) => (
  <Fragment>
    <BackgroundImage src={backgroundImageConfig} />
    {children}
  </Fragment>
);
