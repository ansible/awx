import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { useLocation, useParams } from 'react-router-dom';
import 'styled-components/macro';

import useExpanded from 'hooks/useExpanded';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import DisassociateButton from 'components/DisassociateButton';
import AssociateModal from 'components/AssociateModal';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import { InstanceGroupsAPI, InstancesAPI } from 'api';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import HealthCheckButton from 'components/HealthCheckButton/HealthCheckButton';
import HealthCheckAlert from 'components/HealthCheckAlert';
import InstanceListItem from './InstanceListItem';

const QS_CONFIG = getQSConfig('instance', {
  page: 1,
  page_size: 20,
  order_by: 'hostname',
});

function InstanceList({ instanceGroup }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showHealthCheckAlert, setShowHealthCheckAlert] = useState(false);
  const location = useLocation();
  const { id: instanceGroupId } = useParams();

  const {
    result: {
      instances,
      count,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchInstances,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, responseActions] = await Promise.all([
        InstanceGroupsAPI.readInstances(instanceGroupId, params),
        InstanceGroupsAPI.readInstanceOptions(instanceGroupId),
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
    }, [location.search, instanceGroupId]),
    {
      instances: [],
      count: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(instances);

  useEffect(() => {
    fetchInstances();
  }, [fetchInstances]);

  const {
    error: healthCheckError,
    request: fetchHealthCheck,
    isLoading: isHealthCheckLoading,
  } = useRequest(
    useCallback(async () => {
      const [...response] = await Promise.all(
        selected
          .filter(({ node_type }) => node_type !== 'hop')
          .map(({ id }) => InstancesAPI.healthCheck(id))
      );
      if (response) {
        setShowHealthCheckAlert(true);
      }
    }, [selected])
  );

  const handleHealthCheck = async () => {
    await fetchHealthCheck();
    clearSelected();
  };

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateInstances,
    deletionError: disassociateError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected
            .filter((s) => s.node_type !== 'control')
            .map((instance) =>
              InstanceGroupsAPI.disassociateInstance(
                instanceGroupId,
                instance.id
              )
            )
        ),
      [instanceGroupId, selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchInstances,
    }
  );

  const { request: handleAssociate, error: associateError } = useRequest(
    useCallback(
      async (instancesToAssociate) => {
        await Promise.all(
          instancesToAssociate
            .filter((i) => i.node_type !== 'control' || i.node_type !== 'hop')
            .map((instance) =>
              InstanceGroupsAPI.associateInstance(instanceGroupId, instance.id)
            )
        );
        fetchInstances();
      },
      [instanceGroupId, fetchInstances]
    )
  );

  const handleDisassociate = async () => {
    await disassociateInstances();
    clearSelected();
  };

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError || healthCheckError
  );

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  const fetchInstancesToAssociate = useCallback(
    (params) =>
      InstancesAPI.read(
        mergeParams(params, {
          ...{ not__rampart_groups__id: instanceGroupId },
          ...{ not__node_type: ['hop', 'control'] },
        })
      ),
    [instanceGroupId]
  );

  const readInstancesOptions = useCallback(
    () => InstanceGroupsAPI.readInstanceOptions(instanceGroupId),
    [instanceGroupId]
  );

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(instances);

  return (
    <>
      {showHealthCheckAlert ? (
        <HealthCheckAlert onSetHealthCheckAlert={setShowHealthCheckAlert} />
      ) : null}
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={
          isLoading || isDisassociateLoading || isHealthCheckLoading
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
              ...(canAdd
                ? [
                    <ToolbarAddButton
                      key="associate"
                      onClick={() => setIsModalOpen(true)}
                      defaultLabel={t`Associate`}
                    />,
                  ]
                : []),
              <DisassociateButton
                verifyCannotDisassociate={
                  selected.some((s) => s.node_type === 'control') ||
                  instanceGroup.name === 'controlplane'
                }
                key="disassociate"
                onDisassociate={handleDisassociate}
                itemsToDisassociate={selected}
                modalTitle={t`Disassociate instance from instance group?`}
                isProtectedInstanceGroup={instanceGroup.name === 'controlplane'}
              />,
              <HealthCheckButton
                isDisabled={!canAdd}
                onClick={handleHealthCheck}
                selectedItems={selected}
              />,
            ]}
            emptyStateControls={
              canAdd ? (
                <ToolbarAddButton
                  key="add"
                  onClick={() => setIsModalOpen(true)}
                />
              ) : null
            }
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG} isExpandable>
            <HeaderCell sortKey="hostname">{t`Name`}</HeaderCell>
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
      {isModalOpen && (
        <AssociateModal
          header={t`Instances`}
          fetchRequest={fetchInstancesToAssociate}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={t`Select Instances`}
          optionsRequest={readInstancesOptions}
          displayKey="hostname"
          columns={[
            { key: 'hostname', name: t`Name` },
            { key: 'node_type', name: t`Node Type` },
          ]}
        />
      )}
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {associateError && t`Failed to associate.`}
          {disassociateError &&
            t`Failed to disassociate one or more instances.`}
          {healthCheckError &&
            t`Failed to run a health check on one or more instances.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default InstanceList;
