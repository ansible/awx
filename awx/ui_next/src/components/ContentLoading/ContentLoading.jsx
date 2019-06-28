import React from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { EmptyState, EmptyStateBody } from '@patternfly/react-core';

// TODO: Better loading state - skeleton lines / spinner, etc.
const ContentLoading = ({ i18n }) => (
  <EmptyState>
    <EmptyStateBody>{i18n._(t`Loading...`)}</EmptyStateBody>
  </EmptyState>
);

export { ContentLoading as _ContentLoading };
export default withI18n()(ContentLoading);
