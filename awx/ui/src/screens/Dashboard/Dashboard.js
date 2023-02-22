import React, { useCallback, useEffect, useState } from 'react';
import styled from 'styled-components';

import { t, Trans } from '@lingui/macro';
import {
  Banner,
  Card,
  PageSection,
  Tabs,
  Tab,
  TabTitleText,
} from '@patternfly/react-core';
import { InfoCircleIcon } from '@patternfly/react-icons';

import useRequest from 'hooks/useRequest';
import { DashboardAPI } from 'api';
import ScreenHeader from 'components/ScreenHeader';
import JobList from 'components/JobList';
import ContentLoading from 'components/ContentLoading';
import TemplateList from 'components/TemplateList';
import Count from './shared/Count';
import DashboardGraph from './DashboardGraph';

const Counts = styled.div`
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  grid-gap: var(--pf-global--spacer--lg);

  @media (max-width: 900px) {
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 1fr;
  }
`;

const MainPageSection = styled(PageSection)`
  padding-top: 0;
  padding-bottom: 0;

  & .spacer {
    margin-bottom: var(--pf-global--spacer--lg);
  }
`;

function Dashboard() {
  const [activeTabId, setActiveTabId] = useState(0);

  const {
    isLoading,
    result: countData,
    request: fetchDashboardGraph,
  } = useRequest(
    useCallback(async () => {
      const { data: dataFromCount } = await DashboardAPI.read();

      return dataFromCount;
    }, []),
    {}
  );

  useEffect(() => {
    fetchDashboardGraph();
  }, [fetchDashboardGraph]);
  if (isLoading) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }
  return (
    <>
      <Banner variant="info">
        <Trans>
          <p>
            <InfoCircleIcon /> A tech preview of the new Ansible Automation
            Platform user interface can be found{' '}
            <a href="/controller/dashboard">here</a>.
          </p>
        </Trans>
      </Banner>
      <ScreenHeader
        streamType="all"
        breadcrumbConfig={{ '/home': t`Dashboard` }}
      />
      <PageSection>
        <Counts>
          <Count
            link="/hosts"
            data={countData?.hosts?.total}
            label={t`Hosts`}
          />
          <Count
            failed
            link="/hosts?host.last_job_host_summary__failed=true"
            data={countData?.hosts?.failed}
            label={t`Failed hosts`}
          />
          <Count
            link="/inventories"
            data={countData?.inventories?.total}
            label={t`Inventories`}
          />
          <Count
            failed
            link="/inventories?inventory.inventory_sources_with_failures__gt=0"
            data={countData?.inventories?.inventory_failed}
            label={t`Inventory sync failures`}
          />
          <Count
            link="/projects"
            data={countData?.projects?.total}
            label={t`Projects`}
          />
          <Count
            failed
            link="/projects?project.status__in=failed,canceled"
            data={countData?.projects?.failed}
            label={t`Project sync failures`}
          />
        </Counts>
      </PageSection>
      <MainPageSection>
        <div className="spacer">
          <Card id="dashboard-main-container">
            <Tabs
              aria-label={t`Tabs`}
              activeKey={activeTabId}
              onSelect={(key, eventKey) => setActiveTabId(eventKey)}
              ouiaId="dashboard-tabs"
            >
              <Tab
                aria-label={t`Job status graph tab`}
                eventKey={0}
                title={<TabTitleText>{t`Job status`}</TabTitleText>}
                ouiaId="job-status-graph-tab"
              >
                <DashboardGraph />
              </Tab>
              <Tab
                aria-label={t`Recent Jobs list tab`}
                eventKey={1}
                title={<TabTitleText>{t`Recent Jobs`}</TabTitleText>}
                ouiaId="recent-jobs-list-tab"
              >
                <div>
                  {activeTabId === 1 && (
                    <JobList defaultParams={{ page_size: 5 }} />
                  )}
                </div>
              </Tab>
              <Tab
                aria-label={t`Recent Templates list tab`}
                eventKey={2}
                title={<TabTitleText>{t`Recent Templates`}</TabTitleText>}
                ouiaId="recent-templates-list-tab"
              >
                <div>
                  {activeTabId === 2 && (
                    <TemplateList defaultParams={{ page_size: 5 }} />
                  )}
                </div>
              </Tab>
            </Tabs>
          </Card>
        </div>
      </MainPageSection>
    </>
  );
}

export default Dashboard;
