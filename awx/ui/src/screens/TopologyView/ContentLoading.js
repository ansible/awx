import React from 'react';
import { t } from '@lingui/macro';

import styled from 'styled-components';
import {
  EmptyState as PFEmptyState,
  EmptyStateIcon,
  Text,
  TextContent,
  TextVariants,
  Spinner,
} from '@patternfly/react-core';

import { TopologyIcon as PFTopologyIcon } from '@patternfly/react-icons';

const EmptyState = styled(PFEmptyState)`
  --pf-c-empty-state--m-lg--MaxWidth: none;
  min-height: 250px;
`;

const TopologyIcon = styled(PFTopologyIcon)`
  font-size: 3em;
  fill: #6a6e73;
`;

const ContentLoading = ({ className }) => (
  <EmptyState variant="full" className={className}>
    <TopologyIcon />
    <TextContent>
      <Text
        component={TextVariants.small}
        style={{ fontWeight: 'bold', color: 'black' }}
      >
        {t`Please wait until the topology view is populated...`}
      </Text>
    </TextContent>
    <EmptyStateIcon variant="container" component={Spinner} />
  </EmptyState>
);

export { ContentLoading as _ContentLoading };
export default ContentLoading;
