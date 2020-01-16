import React from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';
import {
  EmptyState as PFEmptyState,
  EmptyStateBody,
} from '@patternfly/react-core';

const EmptyState = styled(PFEmptyState)`
  --pf-c-empty-state--m-lg--MaxWidth: none;
`;

// TODO: Better loading state - skeleton lines / spinner, etc.
const ContentLoading = ({ className, i18n }) => (
  <EmptyState variant="full" className={className}>
    <EmptyStateBody>{i18n._(t`Loading...`)}</EmptyStateBody>
  </EmptyState>
);

export { ContentLoading as _ContentLoading };
export default withI18n()(ContentLoading);
