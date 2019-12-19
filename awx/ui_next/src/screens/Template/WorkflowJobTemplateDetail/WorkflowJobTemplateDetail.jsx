import React, { Component } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { CardBody } from '@patternfly/react-core';

import { DetailList } from '@components/DetailList';

class WorkflowJobTemplateDetail extends Component {
  render() {
    return (
      <CardBody css="padding-top: 20px;">
        <DetailList gutter="sm" />
      </CardBody>
    );
  }
}
export { WorkflowJobTemplateDetail as _WorkflowJobTemplateDetail };
export default withI18n()(withRouter(WorkflowJobTemplateDetail));
