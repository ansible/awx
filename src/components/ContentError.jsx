import React from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody
} from '@patternfly/react-core';
import { ExclamationTriangleIcon } from '@patternfly/react-icons';

// TODO: Pass actual error as prop and display expandable details for network errors.
const ContentError = ({ i18n }) => (
  <EmptyState>
    <EmptyStateIcon icon={ExclamationTriangleIcon} />
    <Title size="lg">
      {i18n._(t`Something went wrong...`)}
    </Title>
    <EmptyStateBody>
      {i18n._(t`There was an error loading this content. Please reload the page.`)}
    </EmptyStateBody>
  </EmptyState>
);

export { ContentError as _ContentError };
export default withI18n()(ContentError);
