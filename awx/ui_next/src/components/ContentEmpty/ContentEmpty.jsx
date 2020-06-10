import React from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';

const ContentEmpty = ({ i18n, title = '', message = '' }) => (
  <EmptyState variant="full">
    <EmptyStateIcon icon={CubesIcon} />
    <Title size="lg" headingLevel="h3">
      {title || i18n._(t`No items found.`)}
    </Title>
    <EmptyStateBody>{message}</EmptyStateBody>
  </EmptyState>
);

export { ContentEmpty as _ContentEmpty };
export default withI18n()(ContentEmpty);
