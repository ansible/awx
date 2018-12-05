import React from 'react';
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
          {'edit view   '}
          <Link to={{ pathname: `/organizations/${match.params.id}`, state: { breadcrumb: parentBreadcrumbObj, organization } }}>
            {'save/cancel and go back to view'}
          </Link>
        </CardBody>
      </Card>
    </PageSection>
  );
};

export default OrganizationEdit;
