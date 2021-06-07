import React from 'react';
import { t } from '@lingui/macro';

import {
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';

const ContentEmpty = ({ title = '', message = '' }) => (
  <EmptyState variant="full">
    <EmptyStateIcon icon={CubesIcon} />
    <Title size="lg" headingLevel="h3">
      {title || t`No items found.`}
    </Title>
    <EmptyStateBody>{message}</EmptyStateBody>
  </EmptyState>
);

export { ContentEmpty as _ContentEmpty };
export default ContentEmpty;
