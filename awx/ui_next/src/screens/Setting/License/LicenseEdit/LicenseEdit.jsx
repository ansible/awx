import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CardBody, CardActionsRow } from '../../../../components/Card';

function LicenseEdit({ i18n }) {
  return (
    <CardBody>
      {i18n._(t`Edit form coming soon :)`)}
      <CardActionsRow>
        <Button
          aria-label={i18n._(t`Cancel`)}
          component={Link}
          to="/settings/license/details"
        >
          {i18n._(t`Cancel`)}
        </Button>
      </CardActionsRow>
    </CardBody>
  );
}

export default withI18n()(LicenseEdit);
