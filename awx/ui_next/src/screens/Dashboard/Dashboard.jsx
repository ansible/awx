import React, { Component, Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class Dashboard extends Component {
  render() {
    const { i18n } = this.props;
    const { light } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed">
          <Title size="2xl">{i18n._(t`Dashboard`)}</Title>
        </PageSection>
        <PageSection />
      </Fragment>
    );
  }
}

export default withI18n()(Dashboard);
