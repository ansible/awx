import React, { useEffect, useCallback, useState } from 'react';
import { useHistory, useLocation, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, mergeParams, parseQueryString } from '@util/qs';
import { GroupsAPI, InventoriesAPI } from '@api';

import useRequest, {
  useDeleteItems,
  useDismissableError,
} from '@util/useRequest';
import useSelected from '@util/useSelected';
import AlertModal from '@components/AlertModal';
import DataListToolbar from '@components/DataListToolbar';
import ErrorDetail from '@components/ErrorDetail';
import PaginatedDataList from '@components/PaginatedDataList';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';
import AssociateModal from './AssociateModal';
import AddHostDropdown from './AddHostDropdown';
import DisassociateButton from './DisassociateButton';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryGroupHostList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { id: inventoryId, groupId } = useParams();
  const location = useLocation();
  const history = useHistory();

  const {
    result: { hosts, hostCount, actions },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        GroupsAPI.readAllHosts(groupId, params),
        InventoriesAPI.readHostsOptions(inventoryId),
      ]);

      return {
        hosts: response.data.results,
        hostCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [groupId, inventoryId, location.search]),
    {
      hosts: [],
      hostCount: 0,
    }
  );

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    hosts
  );

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateHosts,
    deletionError: disassociateError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(host => GroupsAPI.disassociateHost(groupId, host))
      );
    }, [groupId, selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchHosts,
    }
  );

  const handleDisassociate = async () => {
    await disassociateHosts();
    setSelected([]);
  };

  const fetchHostsToAssociate = useCallback(
    params => {
      return InventoriesAPI.readHosts(
        inventoryId,
        mergeParams(params, { not__groups: groupId })
      );
    },
    [groupId, inventoryId]
  );

  const { request: handleAssociate, error: associateError } = useRequest(
    useCallback(
      async hostsToAssociate => {
        await Promise.all(
          hostsToAssociate.map(host =>
            GroupsAPI.associateHost(groupId, host.id)
          )
        );
        fetchHosts();
      },
      [groupId, fetchHosts]
    )
  );

  const { error, dismissError } = useDismissableError(
    associateError || disassociateError
  );

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const addFormUrl = `/inventories/inventory/${inventoryId}/groups/${groupId}/nested_hosts/add`;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
        items={hosts}
        itemCount={hostCount}
        pluralizedItemName={i18n._(t`Hosts`)}
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
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...hosts] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <AddHostDropdown
                      key="associate"
                      onAddExisting={() => setIsModalOpen(true)}
                      onAddNew={() => history.push(addFormUrl)}
                    />,
                  ]
                : []),
              <DisassociateButton
                key="disassociate"
                onDisassociate={handleDisassociate}
                itemsToDisassociate={selected}
                modalTitle={i18n._(t`Disassociate host from group?`)}
                modalNote={i18n._(t`
                        Note that only hosts directly in this group can
                        be disassociated. Hosts in sub-groups must be disassociated
                        directly from the sub-group level that they belong.
                      `)}
              />,
            ]}
          />
        )}
        renderItem={o => (
          <InventoryGroupHostListItem
            key={o.id}
            host={o}
            detailUrl={`/inventories/inventory/${inventoryId}/hosts/${o.id}/details`}
            editUrl={`/inventories/inventory/${inventoryId}/hosts/${o.id}/edit`}
            isSelected={selected.some(row => row.id === o.id)}
            onSelect={() => handleSelect(o)}
          />
        )}
        emptyStateControls={
          canAdd && (
            <AddHostDropdown
              onAddExisting={() => setIsModalOpen(true)}
              onAddNew={() => history.push(addFormUrl)}
            />
          )
        }
      />
      {isModalOpen && (
        <AssociateModal
          header={i18n._(t`Hosts`)}
          fetchRequest={fetchHostsToAssociate}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Hosts`)}
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
            : i18n._(t`Failed to disassociate one or more hosts.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(InventoryGroupHostList);
