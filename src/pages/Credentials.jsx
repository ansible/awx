import React, { Component, Fragment } from 'react';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class Credentials extends Component {
  render () {
    const { light, medium } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light}><Title size="2xl">Credentials</Title></PageSection>
        <PageSection variant={medium} />
      </Fragment>
    );
  }
}

export default Credentials;
