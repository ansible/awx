import React, { useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch, Link } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import { Card, PageSection, DropdownItem } from '@patternfly/react-core';
import { InventoriesAPI } from 'api';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import AlertModal from 'components/AlertModal';
import DatalistToolbar from 'components/DataListToolbar';
import ErrorDetail from 'components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarDeleteButton,
} from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import AddDropDownButton from 'components/AddDropDownButton';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import useWsInventories from './useWsInventories';
import InventoryListItem from './InventoryListItem';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryList() {
  const location = useLocation();
  const match = useRouteMatch();

  const {
    result: {
      results,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchInventories,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        InventoriesAPI.read(params),
        InventoriesAPI.readOptions(),
      ]);
      return {
        results: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter((key) => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [location]),
    {
      results: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  const fetchInventoriesById = useCallback(
    async (ids) => {
      const params = { ...parseQueryString(QS_CONFIG, location.search) };
      params.id__in = ids.join(',');
      const { data } = await InventoriesAPI.read(params);
      return data.results;
    },
    [location.search] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const inventories = useWsInventories(
    results,
    fetchInventories,
    fetchInventoriesById,
    QS_CONFIG
  );

  const { selected, isAllSelected, handleSelect, selectAll, clearSelected } =
    useSelected(inventories);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteInventories,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(selected.map((team) => InventoriesAPI.destroy(team.id))),
      [selected]
    ),
    {
      allItemsSelected: isAllSelected,
    }
  );

  const handleInventoryDelete = async () => {
    await deleteInventories();
    clearSelected();
  };

  const hasContentLoading = isDeleteLoading || isLoading;
  const canAdd = actions && actions.POST;

  const deleteDetailsRequests = relatedResourceDeleteRequests.inventory(
    selected[0]
  );

  const addInventory = t`Add inventory`;
  const addSmartInventory = t`Add smart inventory`;
  const addButton = (
    <AddDropDownButton
      ouiaId="add-inventory-button"
      key="add"
      dropdownItems={[
        <DropdownItem
          ouiaId="add-inventory-item"
          to={`${match.url}/inventory/add/`}
          component={Link}
          key={addInventory}
          aria-label={addInventory}
        >
          {addInventory}
        </DropdownItem>,
        <DropdownItem
          ouiaId="add-smart-inventory-item"
          to={`${match.url}/smart_inventory/add/`}
          component={Link}
          key={addSmartInventory}
          aria-label={addSmartInventory}
        >
          {addSmartInventory}
        </DropdownItem>,
      ]}
    />
  );

  return (
    <PageSection>
      <Card>
        <PaginatedTable
          contentError={contentError}
          hasContentLoading={hasContentLoading}
          items={inventories}
          itemCount={itemCount}
          pluralizedItemName={t`Inventories`}
          qsConfig={QS_CONFIG}
          toolbarSearchColumns={[
            {
              name: t`Name`,
              key: 'name__icontains',
              isDefault: true,
            },
            {
              name: t`Inventory Type`,
              key: 'or__kind',
              options: [
                ['', t`Inventory`],
                ['smart', t`Smart Inventory`],
              ],
            },
            {
              name: t`Organization`,
              key: 'organization__name',
            },
            {
              name: t`Description`,
              key: 'description__icontains',
            },
            {
              name: t`Created By (Username)`,
              key: 'created_by__username__icontains',
            },
            {
              name: t`Modified By (Username)`,
              key: 'modified_by__username__icontains',
            },
          ]}
          toolbarSortColumns={[
            {
              name: t`Name`,
              key: 'name',
            },
          ]}
          toolbarSearchableKeys={searchableKeys}
          toolbarRelatedSearchableKeys={relatedSearchableKeys}
          clearSelected={clearSelected}
          headerRow={
            <HeaderRow qsConfig={QS_CONFIG}>
              <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
              <HeaderCell>{t`Status`}</HeaderCell>
              <HeaderCell>{t`Type`}</HeaderCell>
              <HeaderCell>{t`Organization`}</HeaderCell>
              <HeaderCell>{t`Actions`}</HeaderCell>
            </HeaderRow>
          }
          renderToolbar={(props) => (
            <DatalistToolbar
              {...props}
              isAllSelected={isAllSelected}
              onSelectAll={selectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAdd ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleInventoryDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={t`Inventories`}
                  deleteDetailsRequests={deleteDetailsRequests}
                  deleteMessage={
                    <Plural
                      value={selected.length}
                      one="This inventory is currently being used by some templates. Are you sure you want to delete it?"
                      other="Deleting these inventories could impact some templates that rely on them. Are you sure you want to delete anyway?"
                    />
                  }
                  warningMessage={
                    <Plural
                      value={selected.length}
                      one="The inventory will be in a pending status until the final delete is processed."
                      other="The inventories will be in a pending status until the final delete is processed."
                    />
                  }
                />,
              ]}
            />
          )}
          renderRow={(inventory, index) => (
            <InventoryListItem
              key={inventory.id}
              value={inventory.name}
              inventory={inventory}
              rowIndex={index}
              fetchInventories={fetchInventories}
              detailUrl={
                inventory.kind === 'smart'
                  ? `${match.url}/smart_inventory/${inventory.id}/details`
                  : `${match.url}/inventory/${inventory.id}/details`
              }
              onSelect={() => {
                if (!inventory.pending_deletion) {
                  handleSelect(inventory);
                }
              }}
              isSelected={selected.some((row) => row.id === inventory.id)}
            />
          )}
          emptyStateControls={canAdd && addButton}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="error"
        aria-label={t`Deletion Error`}
        title={t`Error!`}
        onClose={clearDeletionError}
      >
        {t`Failed to delete one or more inventories.`}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </PageSection>
  );
}

export default InventoryList;
