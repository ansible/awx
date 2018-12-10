import React, { Fragment } from 'react';
import { Trans } from '@lingui/macro';
import {
  PageSection,
  PageSectionVariants,
  Title,
} from '@patternfly/react-core';

const { light, medium } = PageSectionVariants;

const OrganizationView = () => (
  <Fragment>
    <PageSection variant={light} className="pf-m-condensed">
      <Title size="2xl">
        <Trans>Organization Add</Trans>
      </Title>
    </PageSection>
    <PageSection variant={medium}>
      This is the add view
    </PageSection>
  </Fragment>
);

export default OrganizationView;
