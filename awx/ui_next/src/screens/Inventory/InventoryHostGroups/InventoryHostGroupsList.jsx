import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
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
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import AssociateModal from '../../../components/AssociateModal';
import DisassociateButton from '../../../components/DisassociateButton';
import InventoryHostGroupItem from './InventoryHostGroupItem';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostGroupsList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { hostId, id: invId } = useParams();
  const { search } = useLocation();

  const {
    result: { groups, itemCount, actions },
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
        actionsResponse,
      ] = await Promise.all([
        HostsAPI.readAllGroups(hostId, params),
        HostsAPI.readGroupsOptions(hostId),
      ]);

      return {
        groups: results,
        itemCount: count,
        actions: actionsResponse.data.actions,
      };
    }, [hostId, search]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      groups: [],
      itemCount: 0,
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
    useCallback(async () => {
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
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
        items={groups}
        itemCount={itemCount}
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
        renderItem={item => (
          <InventoryHostGroupItem
            key={item.id}
            group={item}
            inventoryId={item.summary_fields.inventory.id}
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
                      onClick={() => setIsModalOpen(true)}
                    />,
                  ]
                : []),
              <DisassociateButton
                key="disassociate"
                onDisassociate={handleDisassociate}
                itemsToDisassociate={selected}
                modalTitle={i18n._(t`Disassociate group from host?`)}
                modalNote={i18n._(t`
                  Note that you may still see the group in the list after
                  disassociating if the host is also a member of that group’s 
                  children.  This list shows all groups the host is associated 
                  with directly and indirectly.
                `)}
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
          header={i18n._(t`Groups`)}
          fetchRequest={fetchGroupsToAssociate}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Groups`)}
        />
      )}
      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={i18n._(t`Error!`)}
          variant="error"
        >
          {associateError
            ? i18n._(t`Failed to associate.`)
            : i18n._(t`Failed to disassociate one or more groups.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}
export default withI18n()(InventoryHostGroupsList);
