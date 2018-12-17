import React, { Component, Fragment } from 'react';
import { Trans } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class Dashboard extends Component {
  render () {
    const { light, medium } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed">
          <Title size="2xl">
            <Trans>Dashboard</Trans>
          </Title>
        </PageSection>
        <PageSection variant={medium} />
      </Fragment>
    );
  }
}

export default Dashboard;
