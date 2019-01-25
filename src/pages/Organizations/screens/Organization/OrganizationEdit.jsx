import React from 'react';
import { Trans } from '@lingui/macro';
import {
  Link
} from 'react-router-dom';
import { CardBody } from '@patternfly/react-core';

const OrganizationEdit = ({ match }) => (
  <CardBody>
    <h1><Trans>edit view</Trans></h1>
    <Link to={`/organizations/${match.params.id}`}>
      <Trans>save/cancel and go back to view</Trans>
    </Link>
  </CardBody>
);

export default OrganizationEdit;
