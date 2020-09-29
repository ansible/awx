import React, { useCallback, useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Tooltip,
  DropdownItem,
  ToolbarItem,
} from '@patternfly/react-core';
import { useParams, useLocation, useHistory } from 'react-router-dom';

import { GroupsAPI, InventoriesAPI } from '../../../api';
import useRequest from '../../../util/useRequest';
import { getQSConfig, parseQueryString, mergeParams } from '../../../util/qs';
import useSelected from '../../../util/useSelected';

import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';
import InventoryGroupRelatedGroupListItem from './InventoryRelatedGroupListItem';
import AddDropdown from '../shared/AddDropdown';
import { Kebabified } from '../../../contexts/Kebabified';
import AdHocCommandsButton from '../../../components/AdHocCommands/AdHocCommands';
import AssociateModal from '../../../components/AssociateModal';
import DisassociateButton from '../../../components/DisassociateButton';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});
function InventoryRelatedGroupList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { id: inventoryId, groupId } = useParams();
  const location = useLocation();
  const history = useHistory();
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
  const addButtonOptions = [];

  if (canAdd) {
    addButtonOptions.push(
      {
        onAdd: () => setIsModalOpen(true),
        title: i18n._(t`Add existing group`),
        label: i18n._(t`group`),
        key: 'existing',
      },
      {
        onAdd: () => history.push(addFormUrl),
        title: i18n._(t`Add new group`),
        label: i18n._(t`group`),
        key: 'new',
      }
    );
  }

  const addButton = <AddDropdown key="add" dropdownItems={addButtonOptions} />;

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
              <Kebabified>
                {({ isKebabified }) =>
                  isKebabified ? (
                    <AdHocCommandsButton
                      adHocItems={selected}
                      apiModule={InventoriesAPI}
                      itemId={parseInt(inventoryId, 10)}
                    >
                      {({ openAdHocCommands, isDisabled }) => (
                        <DropdownItem
                          key="run command"
                          onClick={openAdHocCommands}
                          isDisabled={itemCount === 0 || isDisabled}
                        >
                          {i18n._(t`Run command`)}
                        </DropdownItem>
                      )}
                    </AdHocCommandsButton>
                  ) : (
                    <ToolbarItem>
                      <Tooltip
                        content={i18n._(
                          t`Select an inventory source by clicking the check box beside it. The inventory source can be a single host or a selection of multiple hosts.`
                        )}
                        position="top"
                        key="adhoc"
                      >
                        <AdHocCommandsButton
                          css="margin-right: 20px"
                          adHocItems={selected}
                          apiModule={InventoriesAPI}
                          itemId={parseInt(inventoryId, 10)}
                        >
                          {({ openAdHocCommands, isDisabled }) => (
                            <Button
                              variant="secondary"
                              aria-label={i18n._(t`Run command`)}
                              onClick={openAdHocCommands}
                              isDisabled={itemCount === 0 || isDisabled}
                            >
                              {i18n._(t`Run command`)}
                            </Button>
                          )}
                        </AdHocCommandsButton>
                      </Tooltip>
                    </ToolbarItem>
                  )
                }
              </Kebabified>,
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
        emptyStateControls={
          canAdd && (
            <AddDropdown
              key="associate"
              onAddExisting={() => setIsModalOpen(true)}
              onAddNew={() => history.push(addFormUrl)}
              newTitle={i18n._(t`Add new group`)}
              existingTitle={i18n._(t`Add existing group`)}
              label={i18n._(t`group`)}
            />
          )
        }
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
