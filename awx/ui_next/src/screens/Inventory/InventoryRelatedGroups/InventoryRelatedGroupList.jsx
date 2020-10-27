import React, { useCallback, useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useParams, useLocation, Link } from 'react-router-dom';

import { DropdownItem } from '@patternfly/react-core';
import { GroupsAPI, InventoriesAPI } from '../../../api';
import useRequest from '../../../util/useRequest';
import { getQSConfig, parseQueryString, mergeParams } from '../../../util/qs';
import useSelected from '../../../util/useSelected';

import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';
import InventoryGroupRelatedGroupListItem from './InventoryRelatedGroupListItem';
import AddDropDownButton from '../../../components/AddDropDownButton';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import AssociateModal from '../../../components/AssociateModal';
import DisassociateButton from '../../../components/DisassociateButton';
import { toTitleCase } from '../../../util/strings';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});
function InventoryRelatedGroupList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { id: inventoryId, groupId } = useParams();
  const location = useLocation();

  const {
    request: fetchRelated,
    result: {
      groups,
      itemCount,
      relatedSearchableKeys,
      searchableKeys,
      canAdd,
    },
    isLoading,
    error: contentError,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actions] = await Promise.all([
        GroupsAPI.readChildren(groupId, params),
        InventoriesAPI.readGroupsOptions(inventoryId),
      ]);

      return {
        groups: response.data.results,
        itemCount: response.data.count,
        relatedSearchableKeys: (
          actions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(actions.data.actions?.GET || {}).filter(
          key => actions.data.actions?.GET[key].filterable
        ),
        canAdd:
          actions.data.actions &&
          Object.prototype.hasOwnProperty.call(actions.data.actions, 'POST'),
      };
    }, [groupId, location.search, inventoryId]),
    { groups: [], itemCount: 0, canAdd: false }
  );
  useEffect(() => {
    fetchRelated();
  }, [fetchRelated]);

  const fetchGroupsToAssociate = useCallback(
    params => {
      return InventoriesAPI.readGroups(
        inventoryId,
        mergeParams(params, { not__id: inventoryId, not__parents: inventoryId })
      );
    },
    [inventoryId]
  );

  const fetchGroupsOptions = useCallback(
    () => InventoriesAPI.readGroupsOptions(inventoryId),
    [inventoryId]
  );

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    groups
  );

  const addFormUrl = `/home`;

  const addExistingGroup = toTitleCase(i18n._(t`Add Existing Group`));
  const addNewGroup = toTitleCase(i18n._(t`Add New Group`));
  const addButton = (
    <AddDropDownButton
      key="add"
      dropdownItems={[
        <DropdownItem
          key={addExistingGroup}
          onClick={() => setIsModalOpen(true)}
          aria-label={addExistingGroup}
        >
          {addExistingGroup}
        </DropdownItem>,
        <DropdownItem
          component={Link}
          to={`${addFormUrl}`}
          key={addNewGroup}
          aria-label={addNewGroup}
        >
          {addNewGroup}
        </DropdownItem>,
      ]}
    />
  );

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={groups}
        itemCount={itemCount}
        pluralizedItemName={i18n._(t`Related Groups`)}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name__icontains',
            isDefault: true,
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
              ...(canAdd ? [addButton] : []),
              <AdHocCommands
                adHocItems={selected}
                hasListItems={itemCount > 0}
              />,
              <DisassociateButton
                key="disassociate"
                onDisassociate={() => {}}
                itemsToDisassociate={selected}
                modalTitle={i18n._(t`Disassociate related group(s)?`)}
              />,
            ]}
          />
        )}
        renderItem={o => (
          <InventoryGroupRelatedGroupListItem
            key={o.id}
            group={o}
            detailUrl={`/inventories/inventory/${inventoryId}/groups/${o.id}/details`}
            editUrl={`/inventories/inventory/${inventoryId}/groups/${o.id}/edit`}
            isSelected={selected.some(row => row.id === o.id)}
            onSelect={() => handleSelect(o)}
          />
        )}
        emptyStateControls={canAdd && addButton}
      />
      {isModalOpen && (
        <AssociateModal
          header={i18n._(t`Groups`)}
          fetchRequest={fetchGroupsToAssociate}
          optionsRequest={fetchGroupsOptions}
          isModalOpen={isModalOpen}
          onAssociate={() => {}}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Groups`)}
        />
      )}
    </>
  );
}
export default withI18n()(InventoryRelatedGroupList);
