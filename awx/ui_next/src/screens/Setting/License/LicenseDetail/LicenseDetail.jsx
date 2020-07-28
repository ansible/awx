import React from 'react';
import { Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import { CardBody, CardActionsRow } from '../../../../components/Card';

function LicenseDetail({ i18n }) {
  return (
    <CardBody>
      {i18n._(t`Detail coming soon :)`)}
      <CardActionsRow>
        <Button
          aria-label={i18n._(t`Edit`)}
          component={Link}
          to="/settings/license/edit"
        >
          {i18n._(t`Edit`)}
        </Button>
      </CardActionsRow>
    </CardBody>
  );
}

export default withI18n()(LicenseDetail);
