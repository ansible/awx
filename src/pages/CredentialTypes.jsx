import React, { Component, Fragment } from 'react';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class CredentialTypes extends Component {
  render () {
    const { light, medium } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed"><Title size="2xl">Credential Types</Title></PageSection>
        <PageSection variant={medium} />
      </Fragment>
    );
  }
}

export default CredentialTypes;
