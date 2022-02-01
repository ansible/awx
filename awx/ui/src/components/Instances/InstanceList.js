import React, { useCallback, useEffect, useState } from 'react';
import { t } from '@lingui/macro';
import { useLocation, useParams } from 'react-router-dom';
import 'styled-components/macro';

import useExpanded from 'hooks/useExpanded';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
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
import { parseQueryString, mergeParams } from 'util/qs';
import HealthCheckButton from 'components/HealthCheckButton';
import InstanceListItem from './InstanceListItem';

function InstanceList({ headerRow, QS_CONFIG }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { pathname, search } = useLocation();

  const { id } = useParams();
  const isInstanceGroupContext = pathname.includes('instance_groups');
  const readOptions = useCallback(
    (instanceGroupId) =>
      isInstanceGroupContext
        ? InstanceGroupsAPI.readInstanceOptions(instanceGroupId)
        : InstancesAPI.readOptions(),
    [isInstanceGroupContext]
  );
  const readInstances = useCallback(
    (instanceGroupId, params) =>
      isInstanceGroupContext
        ? InstanceGroupsAPI.readInstances(instanceGroupId, params)
        : InstancesAPI.read(),
    [isInstanceGroupContext]
  );
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
      const params = parseQueryString(QS_CONFIG, search);
      const [response, responseActions] = await Promise.all([
        readInstances(id, params),
        readOptions(id),
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
    }, [search, id, readInstances, readOptions, QS_CONFIG]),
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

  const { error: healthCheckError, request: fetchHealthCheck } = useRequest(
    useCallback(async () => {
      await Promise.all(
        selected
          .filter(({ node_type }) => node_type !== 'hop')
          .map(({ id: instId }) => InstancesAPI.healthCheck(instId))
      );
      fetchInstances();
      clearSelected();
    }, [selected, clearSelected, fetchInstances])
  );

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
              InstanceGroupsAPI.disassociateInstance(id, instance.id)
            )
        ),
      [id, selected]
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
            .filter((i) => i.node_type !== 'control')
            .map((instance) =>
              InstanceGroupsAPI.associateInstance(id, instance.id)
            )
        );
        fetchInstances();
      },
      [id, fetchInstances]
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
          ...{ not__rampart_groups__id: id },
          ...{ not__node_type: 'control' },
          ...{ not__node_type: 'hop' },
        })
      ),
    [id]
  );

  const readInstancesOptions = useCallback(
    () => InstanceGroupsAPI.readInstanceOptions(id),
    [id]
  );

  const { expanded, isAllExpanded, handleExpand, expandAll } =
    useExpanded(instances);

  const additionalControls = () => {
    const controls = [
      <HealthCheckButton onClick={fetchHealthCheck} selectedItems={selected} />,
    ];

    if (isInstanceGroupContext) {
      controls.unshift(
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
          verifyCannotDisassociate={selected.some(
            (s) => s.node_type === 'control'
          )}
          key="disassociate"
          onDisassociate={handleDisassociate}
          itemsToDisassociate={selected}
          modalTitle={t`Disassociate instance from instance group?`}
        />
      );
    }
    return controls;
  };

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
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
            additionalControls={additionalControls()}
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
        headerRow={headerRow}
        renderRow={(instance, index) => (
          <InstanceListItem
            isInstanceGroupContext={isInstanceGroupContext}
            detailUrl={`${pathname}/${instance.id}/details`}
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
