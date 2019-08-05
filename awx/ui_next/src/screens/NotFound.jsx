import React from 'react';
import { PageSection, Card } from '@patternfly/react-core';
import { NotFoundError } from '@components/ContentError';

function NotFound() {
  return (
    <PageSection>
      <Card className="awx-c-card">
        <NotFoundError />
      </Card>
    </PageSection>
  );
}

export default NotFound;
