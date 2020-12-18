import React, { useCallback, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Tooltip } from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useSelected from '../../../util/useSelected';
import useRequest from '../../../util/useRequest';
import { InventoriesAPI } from '../../../api';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';

import InventoryGroupItem from './InventoryGroupItem';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function cannotDelete(item) {
  return !item.summary_fields.user_capabilities.delete;
}

function InventoryGroupsList({ i18n }) {
  const location = useLocation();
  const { id: inventoryId } = useParams();

  const {
    result: {
      groups,
      groupCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchData,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, groupOptions] = await Promise.all([
        InventoriesAPI.readGroups(inventoryId, params),
        InventoriesAPI.readGroupsOptions(inventoryId),
      ]);

      return {
        groups: response.data.results,
        groupCount: response.data.count,
        actions: groupOptions.data.actions,
        relatedSearchableKeys: (
          groupOptions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          groupOptions.data.actions?.GET || {}
        ).filter(key => groupOptions.data.actions?.GET[key].filterable),
      };
    }, [inventoryId, location]),
    {
      groups: [],
      groupCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    groups
  );

  const renderTooltip = () => {
    const itemsUnableToDelete = selected
      .filter(cannotDelete)
      .map(item => item.name)
      .join(', ');

    if (selected.some(cannotDelete)) {
      return (
        <div>
          {i18n._(
            t`You do not have permission to delete the following Groups: ${itemsUnableToDelete}`
          )}
        </div>
      );
    }
    if (selected.length) {
      return i18n._(t`Delete`);
    }
    return i18n._(t`Select a row to delete`);
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={groups}
        itemCount={groupCount}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name__icontains',
            isDefault: true,
          },
          {
            name: i18n._(t`Group type`),
            key: 'parents__isnull',
            isBoolean: true,
            booleanLabels: {
              true: i18n._(t`Show only root groups`),
              false: i18n._(t`Show all groups`),
            },
          },
          {
            name: i18n._(t`Created By (Username)`),
            key: 'created_by__username__icontains',
          },
          {
            name: i18n._(t`Modified By (Username)`),
            key: 'modified_by__username__icontains',
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderItem={item => (
          <InventoryGroupItem
            key={item.id}
            group={item}
            inventoryId={inventoryId}
            isSelected={selected.some(row => row.id === item.id)}
            onSelect={() => handleSelect(item)}
          />
        )}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...groups] : [])
            }
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
              <AdHocCommands
                adHocItems={selected}
                hasListItems={groupCount > 0}
              />,
              <Tooltip content={renderTooltip()} position="top" key="delete">
                <InventoryGroupsDeleteModal
                  groups={selected}
                  isDisabled={
                    selected.length === 0 || selected.some(cannotDelete)
                  }
                  onAfterDelete={() => {
                    fetchData();
                    setSelected([]);
                  }}
                />
              </Tooltip>,
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
    </>
  );
}
export default withI18n()(InventoryGroupsList);
