import React, { useEffect, useCallback, useState } from 'react';
import { useLocation, useParams, Link } from 'react-router-dom';

import { t } from '@lingui/macro';
import { DropdownItem } from '@patternfly/react-core';
import { getQSConfig, mergeParams, parseQueryString } from 'util/qs';
import { GroupsAPI, InventoriesAPI } from 'api';

import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';
import useSelected from 'hooks/useSelected';
import AlertModal from 'components/AlertModal';
import DataListToolbar from 'components/DataListToolbar';
import ErrorDetail from 'components/ErrorDetail';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  getSearchableKeys,
} from 'components/PaginatedTable';
import AssociateModal from 'components/AssociateModal';
import DisassociateButton from 'components/DisassociateButton';
import AdHocCommands from 'components/AdHocCommands/AdHocCommands';
import AddDropDownButton from 'components/AddDropDownButton';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryGroupHostList() {
  const [isAdHocLaunchLoading, setIsAdHocLaunchLoading] = useState(false);
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
      moduleOptions,
      isAdHocDisabled,
    },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse, options] = await Promise.all([
        GroupsAPI.readAllHosts(groupId, params),
        InventoriesAPI.readHostsOptions(inventoryId),
        InventoriesAPI.readAdHocOptions(inventoryId),
      ]);

      return {
        moduleOptions: options.data.actions.GET.module_name.choices,
        isAdHocDisabled: !options.data.actions.POST,
        hosts: response.data.results,
        hostCount: response.data.count,
        actions: actionsResponse.data.actions,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [groupId, inventoryId, location.search]),
    {
      moduleOptions: [],
      isAdHocDisabled: true,
      hosts: [],
      hostCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  const { selected, isAllSelected, handleSelect, setSelected } =
    useSelected(hosts);

  useEffect(() => {
    fetchHosts();
  }, [fetchHosts]);

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateHosts,
    deletionError: disassociateErr,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected.map((host) => GroupsAPI.disassociateHost(groupId, host))
        ),
      [groupId, selected]
    ),
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
    (params) =>
      InventoriesAPI.readHosts(
        inventoryId,
        mergeParams(params, { not__groups: groupId })
      ),
    [groupId, inventoryId]
  );

  const fetchHostsOptions = useCallback(
    () => InventoriesAPI.readHostsOptions(inventoryId),
    [inventoryId]
  );

  const { request: handleAssociate, error: associateErr } = useRequest(
    useCallback(
      async (hostsToAssociate) => {
        await Promise.all(
          hostsToAssociate.map((host) =>
            GroupsAPI.associateHost(groupId, host.id)
          )
        );
        fetchHosts();
      },
      [groupId, fetchHosts]
    )
  );

  const { error: associateError, dismissError: dismissAssociateError } =
    useDismissableError(associateErr);
  const { error: disassociateError, dismissError: dismissDisassociateError } =
    useDismissableError(disassociateErr);

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const addFormUrl = `/inventories/inventory/${inventoryId}/groups/${groupId}/nested_hosts/add`;
  const addExistingHost = t`Add existing host`;
  const addNewHost = t`Add new host`;

  const addButton = (
    <AddDropDownButton
      ouiaId="add-hosts-button"
      key="add"
      dropdownItems={[
        <DropdownItem
          onClick={() => setIsModalOpen(true)}
          key={addExistingHost}
          aria-label={addExistingHost}
          ouiaId="add-existing-host-dropdown-item"
        >
          {addExistingHost}
        </DropdownItem>,
        <DropdownItem
          component={Link}
          to={`${addFormUrl}`}
          key={addNewHost}
          aria-label={addNewHost}
          ouiaId="add-new-host-dropdown-item"
        >
          {addNewHost}
        </DropdownItem>,
      ]}
    />
  );
  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={
          isLoading || isDisassociateLoading || isAdHocLaunchLoading
        }
        items={hosts}
        itemCount={hostCount}
        pluralizedItemName={t`Hosts`}
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
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
            <HeaderCell sortKey="description">{t`Description`}</HeaderCell>
            <HeaderCell>{t`Activity`}</HeaderCell>
            <HeaderCell>{t`Actions`}</HeaderCell>
          </HeaderRow>
        }
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            onSelectAll={(isSelected) =>
              setSelected(isSelected ? [...hosts] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd ? [addButton] : []),
              ...(!isAdHocDisabled
                ? [
                    <AdHocCommands
                      adHocItems={selected}
                      hasListItems={hostCount > 0}
                      moduleOptions={moduleOptions}
                      onLaunchLoading={setIsAdHocLaunchLoading}
                    />,
                  ]
                : []),
              <DisassociateButton
                key="disassociate"
                onDisassociate={handleDisassociate}
                itemsToDisassociate={selected}
                modalTitle={t`Disassociate host from group?`}
                modalNote={t`
                        Note that only hosts directly in this group can
                        be disassociated. Hosts in sub-groups must be disassociated
                        directly from the sub-group level that they belong.
                      `}
              />,
            ]}
          />
        )}
        renderRow={(host, index) => (
          <InventoryGroupHostListItem
            key={host.id}
            rowIndex={index}
            host={host}
            detailUrl={`/inventories/inventory/${inventoryId}/hosts/${host.id}/details`}
            editUrl={`/inventories/inventory/${inventoryId}/hosts/${host.id}/edit`}
            isSelected={selected.some((row) => row.id === host.id)}
            onSelect={() => handleSelect(host)}
          />
        )}
        emptyStateControls={canAdd && addButton}
      />
      {isModalOpen && (
        <AssociateModal
          header={t`Hosts`}
          fetchRequest={fetchHostsToAssociate}
          optionsRequest={fetchHostsOptions}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={t`Select Hosts`}
        />
      )}
      {associateError && (
        <AlertModal
          isOpen={associateError}
          onClose={dismissAssociateError}
          title={t`Error!`}
          variant="error"
        >
          {t`Failed to associate.`}
          <ErrorDetail error={associateError} />
        </AlertModal>
      )}
      {disassociateError && (
        <AlertModal
          isOpen={disassociateError}
          onClose={dismissDisassociateError}
          title={t`Error!`}
          variant="error"
        >
          {t`Failed to disassociate one or more hosts.`}
          <ErrorDetail error={disassociateError} />
        </AlertModal>
      )}
    </>
  );
}

export default InventoryGroupHostList;
