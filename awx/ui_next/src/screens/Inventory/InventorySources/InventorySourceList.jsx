import React, { useCallback, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import useRequest, { useDeleteItems } from '@util/useRequest';
import { getQSConfig, parseQueryString } from '@util/qs';
import { InventoriesAPI, InventorySourcesAPI } from '@api';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';
import useSelected from '@util/useSelected';
import DatalistToolbar from '@components/DataListToolbar';
import AlertModal from '@components/AlertModal/AlertModal';
import ErrorDetail from '@components/ErrorDetail/ErrorDetail';
import InventorySourceListItem from './InventorySourceListItem';

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
    error,
    result: { sources, sourceCount, sourceChoices, sourceChoicesOptions },
    request: fetchSources,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);
      const results = await Promise.all([
        InventoriesAPI.readSources(id, params),
        InventorySourcesAPI.readOptions(),
      ]);

      return {
        sources: results[0].data.results,
        sourceCount: results[0].data.count,
        sourceChoices: results[1].data.actions.GET.source.choices,
        sourceChoicesOptions: results[1].data.actions,
      };
    }, [id, search]),
    {
      sources: [],
      sourceCount: 0,
    }
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

  const handleDelete = async () => {
    await handleDeleteSources();
    setSelected([]);
  };
  const canAdd =
    sourceChoicesOptions &&
    Object.prototype.hasOwnProperty.call(sourceChoicesOptions, 'POST');
  const detailUrl = `/inventories/${inventoryType}/${id}/sources/`;
  return (
    <>
      <PaginatedDataList
        contentError={error || deletionError}
        hasContentLoading={isLoading || isDeleteLoading}
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
                ? [<ToolbarAddButton key="add" linkTo={`${detailUrl}add`} />]
                : []),
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={selected}
                pluralizedItemName={i18n._(t`Inventory Sources`)}
              />,
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
              detailUrl={`${detailUrl}${inventorySource.id}`}
              isSelected={selected.some(row => row.id === inventorySource.id)}
            />
          );
        }}
      />
      {deletionError && (
        <AlertModal
          aria-label={i18n._(t`Delete Error`)}
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more Inventory Sources.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}
export default withI18n()(InventorySourceList);
