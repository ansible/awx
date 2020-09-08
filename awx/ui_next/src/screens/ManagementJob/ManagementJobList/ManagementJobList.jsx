import React from 'react';
import { withI18n } from '@lingui/react';
import { Card, PageSection } from '@patternfly/react-core';

function ManagementJobDetails() {
  return (
    <PageSection>
      <Card>Management Job List </Card>
    </PageSection>
  );
}

export default withI18n()(ManagementJobDetails);
