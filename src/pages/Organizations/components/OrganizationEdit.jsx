import React from 'react';
import { Trans } from '@lingui/macro';
import {
  Card,
  CardBody,
  PageSection,
  PageSectionVariants
} from '@patternfly/react-core';
import {
  Link
} from 'react-router-dom';

const OrganizationEdit = ({ match, parentBreadcrumbObj, organization }) => {
  const { medium } = PageSectionVariants;

  return (
    <PageSection variant={medium}>
      <Card className="at-c-orgPane">
        <CardBody>
          <Trans>edit view   </Trans>
          <Link to={{ pathname: `/organizations/${match.params.id}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
            <Trans>save/cancel and go back to view</Trans>
          </Link>
        </CardBody>
      </Card>
    </PageSection>
  );
};

export default OrganizationEdit;
