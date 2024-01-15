import React, { useCallback, useEffect, useState } from 'react';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import {
  Card,
  CardHeader,
  CardActions,
  CardBody,
  CardTitle,
  Flex,
  FlexItem,
  PageSection,
  Select,
  SelectVariant,
  SelectOption,
  Text,
} from '@patternfly/react-core';

import useRequest from 'hooks/useRequest';
import { SubscriptionUsageAPI } from 'api';
import { useUserProfile } from 'contexts/Config';
import ContentLoading from 'components/ContentLoading';
import UsageChart from './ChartComponents/UsageChart';

const GraphCardHeader = styled(CardHeader)`
  margin-bottom: var(--pf-global--spacer--lg);
`;

const ChartCardTitle = styled(CardTitle)`
  padding-right: 24px;
  font-size: 20px;
  font-weight: var(--pf-c-title--m-xl--FontWeight);
`;

const CardText = styled(Text)`
  padding-right: 24px;
`;

const GraphCardActions = styled(CardActions)`
  margin-left: initial;
  padding-left: 0;
`;

function SubscriptionUsageChart() {
  const [isPeriodDropdownOpen, setIsPeriodDropdownOpen] = useState(false);
  const [periodSelection, setPeriodSelection] = useState('year');
  const userProfile = useUserProfile();

  const calculateDateRange = useCallback(() => {
    const today = new Date();
    let date = '';
    switch (periodSelection) {
      case 'year':
        date =
          today.getMonth() < 10
            ? `${today.getFullYear() - 1}-0${today.getMonth() + 1}-01`
            : `${today.getFullYear() - 1}-${today.getMonth() + 1}-01`;
        break;
      case 'two_years':
        date =
          today.getMonth() < 10
            ? `${today.getFullYear() - 2}-0${today.getMonth() + 1}-01`
            : `${today.getFullYear() - 2}-${today.getMonth() + 1}-01`;
        break;
      case 'three_years':
        date =
          today.getMonth() < 10
            ? `${today.getFullYear() - 3}-0${today.getMonth() + 1}-01`
            : `${today.getFullYear() - 3}-${today.getMonth() + 1}-01`;
        break;
      default:
        date =
          today.getMonth() < 10
            ? `${today.getFullYear() - 1}-0${today.getMonth() + 1}-01`
            : `${today.getFullYear() - 1}-${today.getMonth() + 1}-01`;
        break;
    }
    return date;
  }, [periodSelection]);

  const {
    isLoading,
    result: subscriptionUsageChartData,
    request: fetchSubscriptionUsageChart,
  } = useRequest(
    useCallback(async () => {
      const data = await SubscriptionUsageAPI.readSubscriptionUsageChart(
        calculateDateRange()
      );
      return data.data.results;
    }, [calculateDateRange]),
    []
  );

  useEffect(() => {
    fetchSubscriptionUsageChart();
  }, [fetchSubscriptionUsageChart, periodSelection]);

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
    <Card>
      <Flex style={{ justifyContent: 'space-between' }}>
        <FlexItem>
          <ChartCardTitle>{t`Subscription Compliance`}</ChartCardTitle>
        </FlexItem>
        <FlexItem>
          <CardText component="small">
            {t`Last recalculation date:`}{' '}
            {userProfile.systemConfig.HOST_METRIC_SUMMARY_TASK_LAST_TS.slice(
              0,
              10
            )}
          </CardText>
        </FlexItem>
      </Flex>
      <GraphCardHeader>
        <GraphCardActions>
          <Select
            variant={SelectVariant.single}
            placeholderText={t`Select period`}
            aria-label={t`Select period`}
            typeAheadAriaLabel={t`Select period`}
            className="periodSelect"
            onToggle={setIsPeriodDropdownOpen}
            onSelect={(event, selection) => {
              setIsPeriodDropdownOpen(false);
              setPeriodSelection(selection);
            }}
            selections={periodSelection}
            isOpen={isPeriodDropdownOpen}
            noResultsFoundText={t`No results found`}
            ouiaId="subscription-usage-period-select"
          >
            <SelectOption key="year" value="year">
              {t`Past year`}
            </SelectOption>
            <SelectOption key="two_years" value="two_years">
              {t`Past two years`}
            </SelectOption>
            <SelectOption key="three_years" value="three_years">
              {t`Past three years`}
            </SelectOption>
          </Select>
        </GraphCardActions>
      </GraphCardHeader>
      <CardBody>
        <UsageChart
          period={periodSelection}
          height={600}
          id="d3-usage-line-chart-root"
          data={subscriptionUsageChartData}
        />
      </CardBody>
    </Card>
  );
}
export default SubscriptionUsageChart;
