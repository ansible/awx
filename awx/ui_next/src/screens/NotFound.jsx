import React from 'react';
import { PageSection, Card } from '@patternfly/react-core';
import ContentError from '../components/ContentError';

function NotFound() {
  return (
    <PageSection>
      <Card>
        <ContentError isNotFound />
      </Card>
    </PageSection>
  );
}

export default NotFound;
