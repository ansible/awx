import React from 'react';
import styled from 'styled-components';

import { t, Trans } from '@lingui/macro';
import { Banner, Card, PageSection } from '@patternfly/react-core';
import { InfoCircleIcon } from '@patternfly/react-icons';

import { useConfig } from 'contexts/Config';
import ScreenHeader from 'components/ScreenHeader';
import SubscriptionUsageChart from './SubscriptionUsageChart';

const MainPageSection = styled(PageSection)`
  padding-top: 24px;
  padding-bottom: 0;

  & .spacer {
    margin-bottom: var(--pf-global--spacer--lg);
  }
`;

function SubscriptionUsage() {
  const config = useConfig();

  return (
    <>
      {
        <Banner variant="info">
          <Trans>
            <p>
              <InfoCircleIcon /> You are currently viewing the legacy UI
              (deprecated). <a href="/">Enable the new user interface</a>.
            </p>
          </Trans>
        </Banner>
      }
      <ScreenHeader
        streamType="all"
        breadcrumbConfig={{ '/subscription_usage': t`Subscription Usage` }}
      />
      <MainPageSection>
        <div className="spacer">
          <Card id="dashboard-main-container">
            <SubscriptionUsageChart />
          </Card>
        </div>
      </MainPageSection>
    </>
  );
}

export default SubscriptionUsage;
