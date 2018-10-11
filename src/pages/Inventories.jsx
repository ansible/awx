import React, { Component, Fragment } from 'react';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class Inventories extends Component {
  render () {
    const { light, medium } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light}><Title size="2xl">Inventories</Title></PageSection>
        <PageSection variant={medium} />
      </Fragment>
    );
  }
}

export default Inventories;
