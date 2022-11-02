import React, { useCallback, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';

import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';
import { getQSConfig, parseQueryString } from 'util/qs';
import { InventoriesAPI, InventorySourcesAPI } from 'api';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
  ToolbarSyncSourceButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import useSelected from 'hooks/useSelected';
import DatalistToolbar from 'components/DataListToolbar';
import AlertModal from 'components/AlertModal/AlertModal';
import ErrorDetail from 'components/ErrorDetail/ErrorDetail';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import InventorySourceListItem from './InventorySourceListItem';
import useWsInventorySources from './useWsInventorySources';

const QS_CONFIG = getQSConfig('inventory-sources', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventorySourceList() {
  const { inventoryType, id } = useParams();
  const { search } = useLocation();

  const {
    isLoading,
    error: fetchError,
    result: {
      result,
      sourceCount,
      sourceChoices,
      sourceChoicesOptions,
      searchableKeys,
      relatedSearchableKeys,
    },
    request: fetchSources,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);
      const results = await Promise.all([
        InventoriesAPI.readSources(id, params),
        InventorySourcesAPI.readOptions(),
      ]);
      return {
        result: results[0].data.results,
        sourceCount: results[0].data.count,
        sourceChoices: results[1].data.actions.GET.source.choices,
        sourceChoicesOptions: results[1].data.actions,
        searchableKeys: getSearchableKeys(results[1].data.actions?.GET),
        relatedSearchableKeys: (
          results[1]?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
      };
    }, [id, search]),
    {
      result: [],
      sourceCount: 0,
      sourceChoices: [],
      searchableKeys: [],
      relatedSearchableKeys: [],
    }
  );

  const sources = useWsInventorySources(result);

  const canSyncSources =
    sources.length > 0 &&
    sources.every((source) => source.summary_fields.user_capabilities.start);
  const {
    isLoading: isSyncAllLoading,
    error: syncAllError,
    request: syncAll,
  } = useRequest(
    useCallback(async () => {
      if (canSyncSources) {
        await InventoriesAPI.syncAllSources(id);
      }
    }, [id, canSyncSources])
  );

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(sources);

  const {
    isLoading: isDeleteLoading,
    deleteItems: handleDeleteSources,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected.map(({ id: sourceId }) =>
            InventorySourcesAPI.destroy(sourceId)
          ),
          []
        ),
      [selected]
    ),
    {
      fetchItems: fetchSources,
      allItemsSelected: isAllSelected,
      qsConfig: QS_CONFIG,
    }
  );
  const { error: syncError, dismissError } = useDismissableError(syncAllError);

  const deleteRelatedInventoryResources = (resourceId) => [
    InventorySourcesAPI.destroyHosts(resourceId),
    InventorySourcesAPI.destroyGroups(resourceId),
  ];

  const {
    isLoading: deleteRelatedResourcesLoading,
    deletionError: deleteRelatedResourcesError,
    deleteItems: handleDeleteRelatedResources,
  } = useDeleteItems(
    useCallback(
      async () =>
        Promise.all(
          selected
            .map(({ id: resourceId }) =>
              deleteRelatedInventoryResources(resourceId)
            )
            .flat()
        ),
      [selected]
    )
  );

  const handleDelete = async () => {
    await handleDeleteRelatedResources();
    if (!deleteRelatedResourcesError) {
      await handleDeleteSources();
    }
    clearSelected();
  };
  const canAdd =
    sourceChoicesOptions &&
    Object.prototype.hasOwnProperty.call(sourceChoicesOptions, 'POST');
  const listUrl = `/inventories/${inventoryType}/${id}/sources/`;

  const deleteDetailsRequests = relatedResourceDeleteRequests.inventorySource(
    selected[0]?.id
  );
  return (
    <>
      <PaginatedTable
        contentError={fetchError}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        hasContentLoading={
          isLoading ||
          isDeleteLoading ||
          isSyncAllLoading ||
          deleteRelatedResourcesLoading
        }
        items={sources}
        itemCount={sourceCount}
        pluralizedItemName={t`Inventory Sources`}
        qsConfig={QS_CONFIG}
        clearSelected={clearSelected}
        renderToolbar={(props) => (
          <DatalistToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={selectAll}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [<ToolbarAddButton key="add" linkTo={`${listUrl}add`} />]
                : []),
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={selected}
                pluralizedItemName={t`Inventory Sources`}
                deleteDetailsRequests={deleteDetailsRequests}
                deleteMessage={
                  <Plural
                    value={selected.length}
                    one="This inventory source is currently being used by other resources that rely on it. Are you sure you want to delete it?"
                    other="Deleting these inventory sources could impact other resources that rely on them. Are you sure you want to delete anyway"
                  />
                }
              />,
              ...(canSyncSources
                ? [<ToolbarSyncSourceButton onClick={syncAll} />]
                : []),
            ]}
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell>{t`Status`}</HeaderCell>
            <HeaderCell>{t`Type`}</HeaderCell>
            <HeaderCell>{t`Actions`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(inventorySource, index) => {
          const label = sourceChoices.find(
            ([scMatch]) => inventorySource.source === scMatch
          );
          return (
            <InventorySourceListItem
              key={inventorySource.id}
              source={inventorySource}
              onSelect={() => handleSelect(inventorySource)}
              label={label[1]}
              detailUrl={`${listUrl}${inventorySource.id}`}
              isSelected={selected.some((row) => row.id === inventorySource.id)}
              rowIndex={index}
            />
          );
        }}
      />
      {syncError && (
        <AlertModal
          aria-label={t`Sync error`}
          isOpen={syncError}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to sync some or all inventory sources.`}
          <ErrorDetail error={syncError} />
        </AlertModal>
      )}

      {(deletionError || deleteRelatedResourcesError) && (
        <AlertModal
          aria-label={t`Delete error`}
          isOpen={deletionError || deleteRelatedResourcesError}
          variant="error"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more inventory sources.`}
          <ErrorDetail error={deletionError || deleteRelatedResourcesError} />
        </AlertModal>
      )}
    </>
  );
}
export default InventorySourceList;
