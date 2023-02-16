import React, { useCallback, useEffect, useState } from 'react';

import { t } from '@lingui/macro';
import { useParams, useLocation, Link } from 'react-router-dom';

import { DropdownItem } from '@patternfly/react-core';
import { GroupsAPI, InventoriesAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { getQSConfig, parseQueryString, mergeParams } from 'util/qs';
import useSelected from 'hooks/useSelected';

import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';
import AddDropDownButton from 'components/AddDropDownButton';
import AdHocCommands from 'components/AdHocCommands/AdHocCommands';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import AssociateModal from 'components/AssociateModal';
import DisassociateButton from 'components/DisassociateButton';
import InventoryGroupRelatedGroupListItem from './InventoryRelatedGroupListItem';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});
function InventoryRelatedGroupList() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAdHocLaunchLoading, setIsAdHocLaunchLoading] = useState(false);
  const [associateError, setAssociateError] = useState(null);
  const [disassociateError, setDisassociateError] = useState(null);
  const { id: inventoryId, groupId, inventoryType } = useParams();
  const location = useLocation();

  const {
    request: fetchRelated,
    result: {
      groups,
      itemCount,
      relatedSearchableKeys,
      searchableKeys,
      canAdd,
      moduleOptions,
      isAdHocDisabled,
    },
    isLoading,
    error: contentError,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actions, adHocOptions] = await Promise.all([
        GroupsAPI.readChildren(groupId, params),
        InventoriesAPI.readGroupsOptions(inventoryId),
        InventoriesAPI.readAdHocOptions(inventoryId),
      ]);

      return {
        moduleOptions: adHocOptions.data.actions.GET.module_name.choices,
        isAdHocDisabled: !adHocOptions.data.actions.POST,
        groups: response.data.results,
        itemCount: response.data.count,
        relatedSearchableKeys: (actions?.data?.related_search_fields || []).map(
          (val) => val.slice(0, -8)
        ),
        searchableKeys: getSearchableKeys(actions.data.actions?.GET),
        canAdd:
          actions.data.actions &&
          Object.prototype.hasOwnProperty.call(actions.data.actions, 'POST') &&
          inventoryType !== 'constructed_inventory',
      };
    }, [groupId, location.search, inventoryType, inventoryId]),
    {
      groups: [],
      itemCount: 0,
      canAdd: false,
      moduleOptions: [],
      isAdHocDisabled: true,
    }
  );
  useEffect(() => {
    fetchRelated();
  }, [fetchRelated]);

  const fetchGroupsToAssociate = useCallback(
    (params) =>
      GroupsAPI.readPotentialGroups(
        groupId,
        mergeParams(params, { not__id: groupId, not__parents: groupId })
      ),
    [groupId]
  );

  const associateGroup = useCallback(
    async (selectedGroups) => {
      try {
        await Promise.all(
          selectedGroups.map((selected) =>
            GroupsAPI.associateChildGroup(groupId, selected.id)
          )
        );
      } catch (err) {
        setAssociateError(err);
      }
      fetchRelated();
    },
    [groupId, fetchRelated]
  );

  const { selected, isAllSelected, handleSelect, setSelected } =
    useSelected(groups);

  const disassociateGroups = useCallback(async () => {
    try {
      await Promise.all(
        selected.map(({ id: childId }) =>
          GroupsAPI.disassociateChildGroup(parseInt(groupId, 10), childId)
        )
      );
    } catch (err) {
      setDisassociateError(err);
    }
    fetchRelated();
    setSelected([]);
  }, [groupId, selected, setSelected, fetchRelated]);

  const fetchGroupsOptions = useCallback(
    () => InventoriesAPI.readGroupsOptions(inventoryId),
    [inventoryId]
  );

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError
  );

  const addFormUrl = `/inventories/inventory/${inventoryId}/groups/${groupId}/nested_groups/add`;

  const addExistingGroup = t`Add existing group`;
  const addNewGroup = t`Add new group`;
  const addButton = (
    <AddDropDownButton
      key="add"
      ouiaId="add-existing-group-button"
      dropdownItems={[
        <DropdownItem
          key={addExistingGroup}
          onClick={() => setIsModalOpen(true)}
          aria-label={addExistingGroup}
          ouiaId="add-existing-group-dropdown-item"
        >
          {addExistingGroup}
        </DropdownItem>,
        <DropdownItem
          ouiaId="add-new-group-button"
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
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isAdHocLaunchLoading}
        items={groups}
        itemCount={itemCount}
        pluralizedItemName={t`Related Groups`}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: t`Name`,
            key: 'name__icontains',
            isDefault: true,
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
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={(isSelected) =>
              setSelected(isSelected ? [...groups] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd ? [addButton] : []),
              ...(!isAdHocDisabled
                ? [
                    <AdHocCommands
                      adHocItems={selected}
                      hasListItems={itemCount > 0}
                      onLaunchLoading={setIsAdHocLaunchLoading}
                      moduleOptions={moduleOptions}
                    />,
                  ]
                : []),
              <DisassociateButton
                key="disassociate"
                onDisassociate={disassociateGroups}
                itemsToDisassociate={selected}
                modalTitle={t`Disassociate related group(s)?`}
              />,
            ]}
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell>{t`Actions`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(group, index) => (
          <InventoryGroupRelatedGroupListItem
            key={group.id}
            rowIndex={index}
            group={group}
            detailUrl={`/inventories/inventory/${inventoryId}/groups/${group.id}/details`}
            editUrl={`/inventories/inventory/${inventoryId}/groups/${group.id}/edit`}
            isSelected={selected.some((row) => row.id === group.id)}
            onSelect={() => handleSelect(group)}
          />
        )}
        emptyStateControls={canAdd && addButton}
      />
      {isModalOpen && (
        <AssociateModal
          header={t`Groups`}
          fetchRequest={fetchGroupsToAssociate}
          optionsRequest={fetchGroupsOptions}
          isModalOpen={isModalOpen}
          onAssociate={associateGroup}
          onClose={() => setIsModalOpen(false)}
          title={t`Select Groups`}
        />
      )}
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {associateError
            ? t`Failed to associate.`
            : t`Failed to disassociate one or more groups.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}
export default InventoryRelatedGroupList;
