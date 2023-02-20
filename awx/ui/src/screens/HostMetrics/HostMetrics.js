import React, {useCallback, useEffect, useState} from 'react';
import {t} from "@lingui/macro";
import ScreenHeader from 'components/ScreenHeader/ScreenHeader';
import { HostMetricsAPI } from 'api';
import useRequest from 'hooks/useRequest';
import PaginatedTable, {
  HeaderRow,
  HeaderCell
} from 'components/PaginatedTable';
import DataListToolbar from 'components/DataListToolbar';
import { getQSConfig, parseQueryString } from 'util/qs';
import {Card, PageSection} from "@patternfly/react-core";
import { useLocation } from 'react-router-dom';
import HostMetricsListItem from "./HostMetricsListItem";

function HostMetrics() {

  const location = useLocation();

  const [breadcrumbConfig] = useState({
    '/host_metrics': t`Host Metrics`,
  });
  const QS_CONFIG = getQSConfig('host_metrics', {
    page: 1,
    page_size: 20,
    order_by: 'hostname',
  });
  const {
    result: { count, results },
    isLoading,
    error,
    request: readHostMetrics,
  } = useRequest(
      useCallback(async () => {
        const params = parseQueryString(QS_CONFIG, location.search);
        const list = await HostMetricsAPI.read(params);
        return {
          count: list.data.count,
          results: list.data.results
        };
      }, [location.search]),
      { results: [], count: 0 }
  );

  useEffect(() => {
    readHostMetrics();
  }, [readHostMetrics]);

  return(
      <>
      <ScreenHeader
  streamType="none"
  breadcrumbConfig={breadcrumbConfig}
  />
  <PageSection>
  <Card>
  <PaginatedTable
  contentError={error}
  hasContentLoading={isLoading}
  items={results}
  itemCount={count}
  pluralizedItemName={t`Host Metrics`}
  renderRow={(item)=> (<HostMetricsListItem item={item} />)}
  qsConfig={QS_CONFIG}
  toolbarSearchColumns={[{name: t`Hostname`, key: 'hostname__icontains', isDefault: true}]}
  toolbarSearchableKeys={[]}
  toolbarRelatedSearchableKeys={[]}
  renderToolbar={(props) => <DataListToolbar {...props} advancedSearchDisabled={true} fillWidth}
  headerRow={
      <HeaderRow qsConfig={QS_CONFIG}>
      <HeaderCell sortKey="hostname">{t`Hostname`}</HeaderCell>
      <HeaderCell sortKey="first_automation" tooltip={t`When was the host first automated`}>{t`First automated`}</HeaderCell>
      <HeaderCell sortKey="last_automation" tooltip={t`When was the host last automated`}>{t`Last automated`}</HeaderCell>
      <HeaderCell sortKey="automated_counter" tooltip={t`How many times was the host automated`}>{t`Automation`}</HeaderCell>
      <HeaderCell sortKey="used_in_inventories" tooltip={t`How many inventories is the host in, recomputed on a weekly schedule`}>{t`Inventories`}</HeaderCell>
      <HeaderCell sortKey="deleted_counter" tooltip={t`How many times was the host deleted`}>{t`Deleted`}</HeaderCell>
      </HeaderRow>
}
  />
 </Card>
 </PageSection>
  </>
  );
}

export { HostMetrics as _HostMetrics };
export default HostMetrics;
