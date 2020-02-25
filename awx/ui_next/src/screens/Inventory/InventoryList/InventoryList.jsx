import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';

import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';

import { InventoriesAPI } from '@api';
import useRequest, { useDeleteItems } from '@util/useRequest';
import AlertModal from '@components/AlertModal';
import DatalistToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '@components/PaginatedDataList';

import { getQSConfig, parseQueryString } from '@util/qs';
import AddDropDownButton from '@components/AddDropDownButton';
import InventoryListItem from './InventoryListItem';

const QS_CONFIG = getQSConfig('inventory', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();
  const [selected, setSelected] = useState([]);

  const {
    result: { inventories, itemCount, actions },
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
        inventories: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [location]),
    {
      inventories: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchInventories();
  }, [fetchInventories]);

  const isAllSelected =
    selected.length === inventories.length && selected.length > 0;
  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTeams,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(selected.map(team => InventoriesAPI.destroy(team.id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchInventories,
    }
  );

  const handleInventoryDelete = async () => {
    await deleteTeams();
    setSelected([]);
  };

  const hasContentLoading = isDeleteLoading || isLoading;
  const canAdd = actions && actions.POST;

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...inventories] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  const addButton = (
    <AddDropDownButton
      key="add"
      dropdownItems={[
        {
          label: i18n._(t`Inventory`),
          url: `${match.url}/inventory/add/`,
        },
        {
          label: i18n._(t`Smart Inventory`),
          url: `${match.url}/smart_inventory/add/`,
        },
      ]}
    />
  );
  return (
    <PageSection>
      <Card>
        <PaginatedDataList
          contentError={contentError}
          hasContentLoading={hasContentLoading}
          items={inventories}
          itemCount={itemCount}
          pluralizedItemName={i18n._(t`Inventories`)}
          qsConfig={QS_CONFIG}
          onRowClick={handleSelect}
          toolbarSearchColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
              isDefault: true,
            },
            {
              name: i18n._(t`Created By (Username)`),
              key: 'created_by__username',
            },
            {
              name: i18n._(t`Modified By (Username)`),
              key: 'modified_by__username',
            },
          ]}
          toolbarSortColumns={[
            {
              name: i18n._(t`Name`),
              key: 'name',
            },
          ]}
          renderToolbar={props => (
            <DatalistToolbar
              {...props}
              showSelectAll
              showExpandCollapse
              isAllSelected={isAllSelected}
              onSelectAll={handleSelectAll}
              qsConfig={QS_CONFIG}
              additionalControls={[
                ...(canAdd ? [addButton] : []),
                <ToolbarDeleteButton
                  key="delete"
                  onDelete={handleInventoryDelete}
                  itemsToDelete={selected}
                  pluralizedItemName={i18n._(t`Inventories`)}
                />,
              ]}
            />
          )}
          renderItem={inventory => (
            <InventoryListItem
              key={inventory.id}
              value={inventory.name}
              inventory={inventory}
              detailUrl={
                inventory.kind === 'smart'
                  ? `${match.url}/smart_inventory/${inventory.id}/details`
                  : `${match.url}/inventory/${inventory.id}/details`
              }
              onSelect={() => handleSelect(inventory)}
              isSelected={selected.some(row => row.id === inventory.id)}
            />
          )}
          emptyStateControls={canAdd && addButton}
        />
      </Card>
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more inventories.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </PageSection>
  );
}

export default withI18n()(InventoryList);
