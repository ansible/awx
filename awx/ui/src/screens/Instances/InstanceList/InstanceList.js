import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import { useLocation } from 'react-router-dom';
import 'styled-components/macro';
import { PageSection, Card } from '@patternfly/react-core';

import useExpanded from 'hooks/useExpanded';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  getSearchableKeys,
} from 'components/PaginatedTable';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import { InstancesAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import HealthCheckButton from 'components/HealthCheckButton';
import InstanceListItem from './InstanceListItem';

const QS_CONFIG = getQSConfig('instance', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});

function InstanceList() {
  const location = useLocation();

  const {
    result: { instances, count, relatedSearchableKeys, searchableKeys },
    error: contentError,
    isLoading,
    request: fetchInstances,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, responseActions] = await Promise.all([
        InstancesAPI.read(params),
        InstancesAPI.readOptions(),
      ]);
      return {
        instances: response.data.results,
        count: response.data.count,
        actions: responseActions.data.actions,
        relatedSearchableKeys: (
          responseActions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(responseActions.data.actions?.GET),
      };
    }, [location.search]),
    {
      instances: [],
      count: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(instances.filter((i) => i.node_type !== 'hop'));

  useEffect(() => {
    fetchInstances();
  }, [fetchInstances]);

  const {
    error: healthCheckError,
    request: fetchHealthCheck,
    isLoading: isHealthCheckLoading,
  } = useRequest(
    useCallback(async () => {
      await Promise.all(
        selected
          .filter(({ node_type }) => node_type !== 'hop')
          .map(({ id }) => InstancesAPI.healthCheck(id))
      );
      fetchInstances();
    }, [selected, fetchInstances])
  );
  const handleHealthCheck = async () => {
    await fetchHealthCheck();
    clearSelected();
  };
  const { error, dismissError } = useDismissableError(healthCheckError);

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(instances);
  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError}
            hasContentLoading={isLoading || isHealthCheckLoading}
            items={instances}
            itemCount={count}
            pluralizedItemName={t`Instances`}
            qsConfig={QS_CONFIG}
            clearSelected={clearSelected}
            toolbarSearchableKeys={searchableKeys}
            toolbarRelatedSearchableKeys={relatedSearchableKeys}
            toolbarSearchColumns={[
              {
                name: t`Name`,
                key: 'hostname__icontains',
                isDefault: true,
              },
              {
                name: t`Node Type`,
                key: `or__node_type`,
                options: [
                  [`control`, t`Control`],
                  [`execution`, t`Execution`],
                  [`hybrid`, t`Hybrid`],
                  [`hop`, t`Hop`],
                ],
              },
            ]}
            toolbarSortColumns={[
              {
                name: t`Name`,
                key: 'hostname',
              },
            ]}
            renderToolbar={(props) => (
              <DataListToolbar
                {...props}
                isAllSelected={isAllSelected}
                onSelectAll={selectAll}
                isAllExpanded={isAllExpanded}
                onExpandAll={expandAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  <HealthCheckButton
                    onClick={handleHealthCheck}
                    selectedItems={selected}
                  />,
                ]}
              />
            )}
            headerRow={
              <HeaderRow qsConfig={QS_CONFIG} isExpandable>
                <HeaderCell
                  tooltip={t`Cannot run health check on hop nodes.`}
                  sortKey="hostname"
                >{t`Name`}</HeaderCell>
                <HeaderCell sortKey="errors">{t`Status`}</HeaderCell>
                <HeaderCell sortKey="node_type">{t`Node Type`}</HeaderCell>
                <HeaderCell>{t`Capacity Adjustment`}</HeaderCell>
                <HeaderCell>{t`Used Capacity`}</HeaderCell>
                <HeaderCell>{t`Actions`}</HeaderCell>
              </HeaderRow>
            }
            renderRow={(instance, index) => (
              <InstanceListItem
                isExpanded={expanded.some((row) => row.id === instance.id)}
                onExpand={() => handleExpand(instance)}
                key={instance.id}
                value={instance.hostname}
                instance={instance}
                onSelect={() => handleSelect(instance)}
                isSelected={selected.some((row) => row.id === instance.id)}
                fetchInstances={fetchInstances}
                rowIndex={index}
              />
            )}
          />
        </Card>
      </PageSection>
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {t`Failed to run a health check on one or more instances.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default InstanceList;
