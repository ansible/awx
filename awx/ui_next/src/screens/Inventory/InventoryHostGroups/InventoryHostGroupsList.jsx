import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';

import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString, mergeParams } from '../../../util/qs';
import useRequest, {
  useDismissableError,
  useDeleteItems,
} from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { HostsAPI, InventoriesAPI } from '../../../api';
import DataListToolbar from '../../../components/DataListToolbar';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import { ToolbarAddButton } from '../../../components/PaginatedDataList';
import AssociateModal from '../../../components/AssociateModal';
import DisassociateButton from '../../../components/DisassociateButton';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import InventoryHostGroupItem from './InventoryHostGroupItem';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostGroupsList() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAdHocLaunchLoading, setIsAdHocLaunchLoading] = useState(false);
  const { hostId, id: invId } = useParams();
  const { search } = useLocation();

  const {
    result: {
      groups,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
    error: contentError,
    isLoading,
    request: fetchGroups,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);

      const [
        {
          data: { count, results },
        },
        hostGroupOptions,
      ] = await Promise.all([
        HostsAPI.readAllGroups(hostId, params),
        HostsAPI.readGroupsOptions(hostId),
      ]);

      return {
        groups: results,
        itemCount: count,
        actions: hostGroupOptions.data.actions,
        relatedSearchableKeys: (
          hostGroupOptions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          hostGroupOptions.data.actions?.GET || {}
        ).filter(key => hostGroupOptions.data.actions?.GET[key].filterable),
      };
    }, [hostId, search]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      groups: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    groups
  );

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateHosts,
    deletionError: disassociateError,
  } = useDeleteItems(
    useCallback(() => {
      return Promise.all(
        selected.map(group => HostsAPI.disassociateGroup(hostId, group))
      );
    }, [hostId, selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchGroups,
    }
  );

  const handleDisassociate = async () => {
    await disassociateHosts();
    setSelected([]);
  };

  const fetchGroupsToAssociate = useCallback(
    params => {
      return InventoriesAPI.readGroups(
        invId,
        mergeParams(params, { not__hosts: hostId })
      );
    },
    [invId, hostId]
  );

  const fetchGroupsOptions = useCallback(
    () => InventoriesAPI.readGroupsOptions(invId),
    [invId]
  );

  const { request: handleAssociate, error: associateError } = useRequest(
    useCallback(
      async groupsToAssociate => {
        await Promise.all(
          groupsToAssociate.map(group =>
            HostsAPI.associateGroup(hostId, group.id)
          )
        );
        fetchGroups();
      },
      [hostId, fetchGroups]
    )
  );

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError
  );

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={
          isLoading || isDisassociateLoading || isAdHocLaunchLoading
        }
        items={groups}
        itemCount={itemCount}
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
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell>{t`Actions`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(item, index) => (
          <InventoryHostGroupItem
            key={item.id}
            group={item}
            inventoryId={item.summary_fields.inventory.id}
            isSelected={selected.some(row => row.id === item.id)}
            onSelect={() => handleSelect(item)}
            rowIndex={index}
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
                      onClick={() => setIsModalOpen(true)}
                    />,
                  ]
                : []),
              <AdHocCommands
                adHocItems={selected}
                hasListItems={itemCount > 0}
                onLaunchLoading={setIsAdHocLaunchLoading}
              />,
              <DisassociateButton
                key="disassociate"
                onDisassociate={handleDisassociate}
                itemsToDisassociate={selected}
                modalTitle={t`Disassociate group from host?`}
                modalNote={t`
                  Note that you may still see the group in the list after
                  disassociating if the host is also a member of that group’s
                  children.  This list shows all groups the host is associated
                  with directly and indirectly.
                `}
              />,
            ]}
          />
        )}
        emptyStateControls={
          canAdd ? (
            <ToolbarAddButton key="add" onClick={() => setIsModalOpen(true)} />
          ) : null
        }
      />
      {isModalOpen && (
        <AssociateModal
          header={t`Groups`}
          fetchRequest={fetchGroupsToAssociate}
          optionsRequest={fetchGroupsOptions}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
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
export default InventoryHostGroupsList;
