import React, { Fragment } from 'react';

import { BackgroundImage, BackgroundImageSrc } from '@patternfly/react-core';
import bgFilter from '@patternfly/patternfly/assets/images/background-filter.svg';

const backgroundImageConfig = {
  [BackgroundImageSrc.xs]: '/assets/images/pfbg_576.jpg',
  [BackgroundImageSrc.xs2x]: '/assets/images/pfbg_576@2x.jpg',
  [BackgroundImageSrc.sm]: '/assets/images/pfbg_768.jpg',
  [BackgroundImageSrc.sm2x]: '/assets/images/pfbg_768@2x.jpg',
  [BackgroundImageSrc.lg]: '/assets/images/pfbg_2000.jpg',
  [BackgroundImageSrc.filter]: `${bgFilter}#image_overlay`,
};

export default ({ children }) => (
  <Fragment>
    <BackgroundImage src={backgroundImageConfig} />
    {children}
  </Fragment>
);
