import React from 'react';
import { t } from '@lingui/macro';
import {
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';

const ContentEmpty = ({
  title = '',
  message = '',
  icon = CubesIcon,
  className = '',
}) => (
  <EmptyState variant="full" className={className}>
    <EmptyStateIcon icon={icon} />
    <Title size="lg" headingLevel="h3">
      {title || t`No items found.`}
    </Title>
    <EmptyStateBody>{message}</EmptyStateBody>
  </EmptyState>
);

export { ContentEmpty as _ContentEmpty };
export default ContentEmpty;
