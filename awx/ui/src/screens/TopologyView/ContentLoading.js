import React from 'react';
import { t } from '@lingui/macro';

import styled from 'styled-components';
import {
  EmptyState as PFEmptyState,
  Progress,
  ProgressMeasureLocation,
  Text,
  TextContent,
  TextVariants,
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

const ContentLoading = ({ className, progress }) => (
  <EmptyState variant="full" className={className}>
    <TopologyIcon />
    <Progress
      value={progress}
      measureLocation={ProgressMeasureLocation.inside}
      aria-label={t`content-loading-in-progress`}
      style={{ margin: '20px' }}
    />
    <TextContent style={{ margin: '20px' }}>
      <Text
        component={TextVariants.small}
        style={{ fontWeight: 'bold', color: 'black' }}
      >
        {t`Please wait until the topology view is populated...`}
      </Text>
    </TextContent>
  </EmptyState>
);

export default ContentLoading;
