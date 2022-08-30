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
  ToolbarAddButton,
} from 'components/PaginatedTable';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { useConfig } from 'contexts/Config';
import useRequest, {
  useDismissableError,
  useDeleteItems,
} from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import { InstancesAPI, SettingsAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import HealthCheckButton from 'components/HealthCheckButton';
import InstanceListItem from './InstanceListItem';
import RemoveInstanceButton from '../Shared/RemoveInstanceButton';

const QS_CONFIG = getQSConfig('instance', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});

function InstanceList() {
  const location = useLocation();
  const { me } = useConfig();

  const {
    result: { instances, count, relatedSearchableKeys, searchableKeys, isK8s },
    error: contentError,
    isLoading,
    request: fetchInstances,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, responseActions, sysSettings] = await Promise.all([
        InstancesAPI.read(params),
        InstancesAPI.readOptions(),
        SettingsAPI.readCategory('system'),
      ]);
      return {
        instances: response.data.results,
        isK8s: sysSettings.data.IS_K8S,
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
      isK8s: false,
    }
  );

  useEffect(() => {
    fetchInstances();
  }, [fetchInstances]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(instances.filter((i) => i.node_type !== 'hop'));

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

  const {
    isLoading: isRemoveLoading,
    deleteItems: handleRemoveInstances,
    deletionError: removeError,
    clearDeletionError,
  } = useDeleteItems(
    () =>
      Promise.all(
        selected.map(({ id }) => InstancesAPI.deprovisionInstance(id))
      ),
    { fetchItems: fetchInstances }
  );

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedTable
            contentError={contentError || removeError}
            hasContentLoading={
              isLoading || isHealthCheckLoading || isRemoveLoading
            }
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
                  ...(isK8s && me.is_superuser
                    ? [
                        <ToolbarAddButton
                          ouiaId="instances-add-button"
                          key="add"
                          linkTo="/instances/add"
                        />,
                        <RemoveInstanceButton
                          itemsToRemove={selected}
                          isK8s={isK8s}
                          key="remove"
                          onRemove={handleRemoveInstances}
                        />,
                      ]
                    : []),
                  <HealthCheckButton
                    onClick={handleHealthCheck}
                    key="healthCheck"
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
      {removeError && (
        <AlertModal
          isOpen={removeError}
          variant="error"
          aria-label={t`Removal Error`}
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to remove one or more instances.`}
          <ErrorDetail error={removeError} />
        </AlertModal>
      )}
    </>
  );
}

export default InstanceList;
