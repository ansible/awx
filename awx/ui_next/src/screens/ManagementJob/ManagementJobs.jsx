import React, { Component, Fragment } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import Breadcrumbs from '../../components/Breadcrumbs';

class ManagementJobs extends Component {
  render() {
    const { i18n } = this.props;

    return (
      <Fragment>
        <Breadcrumbs
          breadcrumbConfig={{ '/management_jobs': i18n._(t`Management Jobs`) }}
        />
      </Fragment>
    );
  }
}

export default withI18n()(ManagementJobs);
