import React, { Component, Fragment } from 'react';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class License extends Component {
  render () {
    const { light, medium } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed"><Title size="2xl">License</Title></PageSection>
        <PageSection variant={medium} />
      </Fragment>
    );
  }
}

export default License;
