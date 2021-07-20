import React from 'react';

import styled from 'styled-components';
import {
  EmptyState as PFEmptyState,
  EmptyStateIcon,
  Spinner,
} from '@patternfly/react-core';

const EmptyState = styled(PFEmptyState)`
  --pf-c-empty-state--m-lg--MaxWidth: none;
  min-height: 250px;
`;

// TODO: Better loading state - skeleton lines / spinner, etc.
const ContentLoading = ({ className }) => (
  <EmptyState variant="full" className={className}>
    <EmptyStateIcon variant="container" component={Spinner} />
  </EmptyState>
);

export { ContentLoading as _ContentLoading };
export default ContentLoading;
