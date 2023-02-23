import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { Tooltip } from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from 'util/qs';
import useSelected from 'hooks/useSelected';
import useRequest from 'hooks/useRequest';
import { InventoriesAPI } from 'api';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import AdHocCommands from 'components/AdHocCommands/AdHocCommands';
import InventoryGroupItem from './InventoryGroupItem';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function cannotDelete(item) {
  return !item.summary_fields.user_capabilities.delete;
}

function InventoryGroupsList() {
  const location = useLocation();
  const { id: inventoryId, inventoryType } = useParams();
  const [isAdHocLaunchLoading, setIsAdHocLaunchLoading] = useState(false);

  const {
    result: {
      groups,
      groupCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
      moduleOptions,
      isAdHocDisabled,
    },
    error: contentError,
    isLoading,
    request: fetchData,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, groupOptions, options] = await Promise.all([
        InventoriesAPI.readGroups(inventoryId, params),
        InventoriesAPI.readGroupsOptions(inventoryId),
        InventoriesAPI.readAdHocOptions(inventoryId),
      ]);

      return {
        moduleOptions: options.data.actions.GET.module_name.choices,
        isAdHocDisabled: !options.data.actions.POST,
        groups: response.data.results,
        groupCount: response.data.count,
        actions: groupOptions.data.actions,
        relatedSearchableKeys: (
          groupOptions?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(groupOptions.data.actions?.GET),
      };
    }, [inventoryId, location]),
    {
      groups: [],
      groupCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
      moduleOptions: [],
      isAdHocDisabled: true,
    }
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(groups);

  const renderTooltip = () => {
    const itemsUnableToDelete = selected
      .filter(cannotDelete)
      .map((item) => item.name)
      .join(', ');

    if (selected.some(cannotDelete)) {
      return (
        <div>
          {t`You do not have permission to delete the following Groups: ${itemsUnableToDelete}`}
        </div>
      );
    }
    if (selected.length) {
      return t`Delete`;
    }
    return t`Select a row to delete`;
  };
  const isNotConstructedInventory = inventoryType !== 'constructed_inventory';
  const canAdd =
    actions &&
    Object.prototype.hasOwnProperty.call(actions, 'POST') &&
    isNotConstructedInventory;

  return (
    <PaginatedTable
      contentError={contentError}
      hasContentLoading={isLoading || isAdHocLaunchLoading}
      items={groups}
      itemCount={groupCount}
      qsConfig={QS_CONFIG}
      clearSelected={clearSelected}
      toolbarSearchColumns={[
        {
          name: t`Name`,
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: t`Group type`,
          key: 'parents__isnull',
          options: [['true', t`Show only root groups`]],
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
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
      headerRow={
        <HeaderRow qsConfig={QS_CONFIG}>
          <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
          {isNotConstructedInventory && <HeaderCell>{t`Actions`}</HeaderCell>}
        </HeaderRow>
      }
      renderRow={(item, index) => (
        <InventoryGroupItem
          key={item.id}
          group={item}
          isSelected={selected.some((row) => row.id === item.id)}
          onSelect={() => handleSelect(item)}
          rowIndex={index}
        />
      )}
      renderToolbar={(props) => (
        <DataListToolbar
          {...props}
          isAllSelected={isAllSelected}
          onSelectAll={selectAll}
          qsConfig={QS_CONFIG}
          additionalControls={[
            ...(canAdd
              ? [
                  <ToolbarAddButton
                    key="add"
                    linkTo={`/inventories/inventory/${inventoryId}/groups/add`}
                  />,
                ]
              : []),
            ...(!isAdHocDisabled
              ? [
                  <AdHocCommands
                    adHocItems={selected}
                    hasListItems={groupCount > 0}
                    onLaunchLoading={setIsAdHocLaunchLoading}
                    moduleOptions={moduleOptions}
                  />,
                ]
              : []),
            ...(isNotConstructedInventory
              ? [
                  <Tooltip
                    content={renderTooltip()}
                    position="top"
                    key="delete"
                  >
                    <div>
                      <InventoryGroupsDeleteModal
                        groups={selected}
                        isDisabled={
                          selected.length === 0 || selected.some(cannotDelete)
                        }
                        onAfterDelete={() => {
                          fetchData();
                          clearSelected();
                        }}
                      />
                    </div>
                  </Tooltip>,
                ]
              : []),
          ]}
        />
      )}
      emptyStateControls={
        canAdd && (
          <ToolbarAddButton
            key="add"
            linkTo={`/inventories/inventory/${inventoryId}/groups/add`}
          />
        )
      }
    />
  );
}
export default InventoryGroupsList;
