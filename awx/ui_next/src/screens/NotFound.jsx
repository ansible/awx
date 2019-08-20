import React from 'react';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '@components/ContentError';

function NotFound() {
  return (
    <PageSection>
      <Card className="awx-c-card">
        <ContentError isNotFound />
      </Card>
    </PageSection>
  );
}

export default NotFound;
