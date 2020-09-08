import React from 'react';
import { withI18n } from '@lingui/react';

import { CardBody } from '../../../components/Card';

function ManagementJobDetails() {
  return <CardBody>Management Job Details</CardBody>;
}

export default withI18n()(ManagementJobDetails);
