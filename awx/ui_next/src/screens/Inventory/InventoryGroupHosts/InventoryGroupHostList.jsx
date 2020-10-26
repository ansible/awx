import React, { useEffect, useCallback, useState } from 'react';
import { useLocation, useParams, Link } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { DropdownItem } from '@patternfly/react-core';
import { getQSConfig, mergeParams, parseQueryString } from '../../../util/qs';
import { GroupsAPI, InventoriesAPI } from '../../../api';

import useRequest, {
  useDeleteItems,
  useDismissableError,
} from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedDataList from '../../../components/PaginatedDataList';
import AssociateModal from '../../../components/AssociateModal';
import DisassociateButton from '../../../components/DisassociateButton';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';
import AddDropDownButton from '../../../components/AddDropDownButton';
import { toTitleCase } from '../../../util/strings';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryGroupHostList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { id: inventoryId, groupId } = useParams();
  const location = useLocation();

  const {
    result: {
      hosts,
      hostCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
    },
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
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [groupId, inventoryId, location.search]),
    {
      hosts: [],
      hostCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
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
    deletionError: disassociateErr,
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

  const fetchHostsOptions = useCallback(
    () => InventoriesAPI.readHostsOptions(inventoryId),
    [inventoryId]
  );

  const { request: handleAssociate, error: associateErr } = useRequest(
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

  const {
    error: associateError,
    dismissError: dismissAssociateError,
  } = useDismissableError(associateErr);
  const {
    error: disassociateError,
    dismissError: dismissDisassociateError,
  } = useDismissableError(disassociateErr);

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const addFormUrl = `/inventories/inventory/${inventoryId}/groups/${groupId}/nested_hosts/add`;
  const addExistingHost = toTitleCase(i18n._(t`Add Existing Host`));
  const addNewHost = toTitleCase(i18n._(t`Add New Host`));

  const addButton = (
    <AddDropDownButton
      key="add"
      dropdownItems={[
        <DropdownItem
          onClick={() => setIsModalOpen(true)}
          key={addExistingHost}
          aria-label={addExistingHost}
        >
          {addExistingHost}
        </DropdownItem>,
        <DropdownItem
          component={Link}
          to={`${addFormUrl}`}
          key={addNewHost}
          aria-label={addNewHost}
        >
          {addNewHost}
        </DropdownItem>,
      ]}
    />
  );
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
              setSelected(isSelected ? [...hosts] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd ? [addButton] : []),
              <AdHocCommands
                adHocItems={selected}
                hasListItems={hostCount > 0}
              />,
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
        emptyStateControls={canAdd && addButton}
      />
      {isModalOpen && (
        <AssociateModal
          header={i18n._(t`Hosts`)}
          fetchRequest={fetchHostsToAssociate}
          optionsRequest={fetchHostsOptions}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Hosts`)}
        />
      )}
      {associateError && (
        <AlertModal
          isOpen={associateError}
          onClose={dismissAssociateError}
          title={i18n._(t`Error!`)}
          variant="error"
        >
          {i18n._(t`Failed to associate.`)}
          <ErrorDetail error={associateError} />
        </AlertModal>
      )}
      {disassociateError && (
        <AlertModal
          isOpen={disassociateError}
          onClose={dismissDisassociateError}
          title={i18n._(t`Error!`)}
          variant="error"
        >
          {i18n._(t`Failed to disassociate one or more hosts.`)}
          <ErrorDetail error={disassociateError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(InventoryGroupHostList);
