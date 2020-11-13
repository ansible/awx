import React, { useCallback, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';

import useRequest, {
  useDeleteItems,
  useDismissableError,
} from '../../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { InventoriesAPI, InventorySourcesAPI } from '../../../api';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import useSelected from '../../../util/useSelected';
import DatalistToolbar from '../../../components/DataListToolbar';
import AlertModal from '../../../components/AlertModal/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail/ErrorDetail';
import InventorySourceListItem from './InventorySourceListItem';
import useWsInventorySources from './useWsInventorySources';

const QS_CONFIG = getQSConfig('inventory', {
  not__source: '',
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventorySourceList({ i18n }) {
  const { inventoryType, id } = useParams();
  const { search } = useLocation();

  const {
    isLoading,
    error: fetchError,
    result: { result, sourceCount, sourceChoices, sourceChoicesOptions },
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
      };
    }, [id, search]),
    {
      result: [],
      sourceCount: 0,
      sourceChoices: [],
    }
  );

  const sources = useWsInventorySources(result);

  const canSyncSources =
    sources.length > 0 &&
    sources.every(source => source.summary_fields.user_capabilities.start);
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

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    sources
  );

  const {
    isLoading: isDeleteLoading,
    deleteItems: handleDeleteSources,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ id: sourceId }) =>
          InventorySourcesAPI.destroy(sourceId)
        ),
        []
      );
    }, [selected]),
    {
      fetchItems: fetchSources,
      allItemsSelected: isAllSelected,
      qsConfig: QS_CONFIG,
    }
  );
  const { error: syncError, dismissError } = useDismissableError(syncAllError);

  const deleteRelatedInventoryResources = resourceId => {
    return [
      InventorySourcesAPI.destroyHosts(resourceId),
      InventorySourcesAPI.destroyGroups(resourceId),
    ];
  };

  const {
    isLoading: deleteRelatedResourcesLoading,
    deletionError: deleteRelatedResourcesError,
    deleteItems: handleDeleteRelatedResources,
  } = useDeleteItems(
    useCallback(async () => {
      return (
        Promise.all(
          selected
            .map(({ id: resourceId }) =>
              deleteRelatedInventoryResources(resourceId)
            )
            .flat()
        ),
        []
      );
    }, [selected])
  );

  const handleDelete = async () => {
    await handleDeleteRelatedResources();
    if (!deleteRelatedResourcesError) {
      await handleDeleteSources();
    }
    setSelected([]);
  };
  const canAdd =
    sourceChoicesOptions &&
    Object.prototype.hasOwnProperty.call(sourceChoicesOptions, 'POST');
  const listUrl = `/inventories/${inventoryType}/${id}/sources/`;
  return (
    <>
      <PaginatedDataList
        contentError={fetchError}
        hasContentLoading={
          isLoading ||
          isDeleteLoading ||
          isSyncAllLoading ||
          deleteRelatedResourcesLoading
        }
        items={sources}
        itemCount={sourceCount}
        pluralizedItemName={i18n._(t`Inventory Sources`)}
        qsConfig={QS_CONFIG}
        renderToolbar={props => (
          <DatalistToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...sources] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [<ToolbarAddButton key="add" linkTo={`${listUrl}add`} />]
                : []),
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={selected}
                pluralizedItemName={i18n._(t`Inventory Sources`)}
              />,
              ...(canSyncSources
                ? [
                    <Tooltip
                      key="update"
                      content={i18n._(t`Sync all sources`)}
                      position="top"
                    >
                      <Button
                        onClick={syncAll}
                        aria-label={i18n._(t`Sync all`)}
                        variant="secondary"
                      >
                        {i18n._(t`Sync all`)}
                      </Button>
                    </Tooltip>,
                  ]
                : []),
            ]}
          />
        )}
        renderItem={inventorySource => {
          let label;
          sourceChoices.forEach(([scMatch, scLabel]) => {
            if (inventorySource.source === scMatch) {
              label = scLabel;
            }
          });
          return (
            <InventorySourceListItem
              key={inventorySource.id}
              source={inventorySource}
              onSelect={() => handleSelect(inventorySource)}
              label={label}
              detailUrl={`${listUrl}${inventorySource.id}`}
              isSelected={selected.some(row => row.id === inventorySource.id)}
            />
          );
        }}
      />
      {syncError && (
        <AlertModal
          aria-label={i18n._(t`Sync error`)}
          isOpen={syncError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to sync some or all inventory sources.`)}
          <ErrorDetail error={syncError} />
        </AlertModal>
      )}

      {(deletionError || deleteRelatedResourcesError) && (
        <AlertModal
          aria-label={i18n._(t`Delete error`)}
          isOpen={deletionError || deleteRelatedResourcesError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more inventory sources.`)}
          <ErrorDetail error={deletionError || deleteRelatedResourcesError} />
        </AlertModal>
      )}
    </>
  );
}
export default withI18n()(InventorySourceList);
