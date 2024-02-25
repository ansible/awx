import React from 'react';
import styled from 'styled-components';

import { t, Trans } from '@lingui/macro';
import { Banner, Card, PageSection } from '@patternfly/react-core';
import { InfoCircleIcon } from '@patternfly/react-icons';

import { useConfig } from 'contexts/Config';
import useBrandName from 'hooks/useBrandName';
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
  const brandName = useBrandName();

  return (
    <>
      {config?.ui_next && (
        <Banner variant="info">
          <Trans>
            <p>
              <InfoCircleIcon /> A tech preview of the new {brandName} user
              interface can be found <a href="/ui_next/dashboard">here</a>.
            </p>
          </Trans>
        </Banner>
      )}
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
