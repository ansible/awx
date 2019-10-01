import React, { Component, Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

class InstanceGroups extends Component {
  render() {
    const { i18n } = this.props;
    const { light } = PageSectionVariants;

    return (
      <Fragment>
        <PageSection variant={light} className="pf-m-condensed">
          <Title size="2xl">{i18n._(t`Instance Groups`)}</Title>
        </PageSection>
        <PageSection />
      </Fragment>
    );
  }
}

export default withI18n()(InstanceGroups);
