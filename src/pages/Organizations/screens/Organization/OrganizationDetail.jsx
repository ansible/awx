import React from 'react';
import { withRouter, Link } from 'react-router-dom';
import { Trans } from '@lingui/macro';
import { CardBody } from '@patternfly/react-core';

const OrganizationDetail = ({ match, organization }) => (
  <CardBody>
    <h1><Trans>{`${organization && organization.name} Detail View`}</Trans></h1>
    <Link to={`/organizations/${match.params.id}/edit`}>
      <Trans>Edit Details</Trans>
    </Link>
  </CardBody>
);

export default withRouter(OrganizationDetail);
