import React, { Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '../../components/Breadcrumbs';

function ManagementJobs({ i18n }) {
  return (
    <Fragment>
      <Breadcrumbs
        breadcrumbConfig={{ '/management_jobs': i18n._(t`Management Jobs`) }}
      />
    </Fragment>
  );
}

export default withI18n()(ManagementJobs);
