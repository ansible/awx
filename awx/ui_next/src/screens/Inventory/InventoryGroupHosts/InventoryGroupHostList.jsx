import React, { useEffect, useCallback, useState } from 'react';
import { useHistory, useLocation, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Tooltip,
  DropdownItem,
  ToolbarItem,
} from '@patternfly/react-core';
import { getQSConfig, mergeParams, parseQueryString } from '../../../util/qs';
import { GroupsAPI, InventoriesAPI, CredentialTypesAPI } from '../../../api';

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
import { Kebabified } from '../../../contexts/Kebabified';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import InventoryGroupHostListItem from './InventoryGroupHostListItem';
import AddHostDropdown from './AddHostDropdown';

const QS_CONFIG = getQSConfig('host', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryGroupHostList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAdHocCommandsOpen, setIsAdHocCommandsOpen] = useState(false);
  const { id: inventoryId, groupId } = useParams();
  const location = useLocation();
  const history = useHistory();

  const {
    result: {
      hosts,
      hostCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
      moduleOptions,
      credentialTypeId,
      isAdHocDisabled,
    },
    error: contentError,
    isLoading,
    request: fetchHosts,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        response,
        actionsResponse,
        adHocOptions,
        cred,
      ] = await Promise.all([
        GroupsAPI.readAllHosts(groupId, params),
        InventoriesAPI.readHostsOptions(inventoryId),
        InventoriesAPI.readAdHocOptions(inventoryId),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
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
        moduleOptions: adHocOptions.data.actions.GET.module_name.choices,
        credentialTypeId: cred.data.results[0].id,
        isAdHocDisabled: !adHocOptions.data.actions.POST,
      };
    }, [groupId, inventoryId, location.search]),
    {
      hosts: [],
      hostCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
      moduleOptions: [],
      isAdHocDisabled: true,
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
              ...(canAdd
                ? [
                    <AddHostDropdown
                      key="associate"
                      onAddExisting={() => setIsModalOpen(true)}
                      onAddNew={() => history.push(addFormUrl)}
                    />,
                  ]
                : []),
              <Kebabified>
                {({ isKebabified }) =>
                  isKebabified ? (
                    <DropdownItem
                      variant="secondary"
                      aria-label={i18n._(t`Run command`)}
                      onClick={() => setIsAdHocCommandsOpen(true)}
                      isDisabled={hostCount === 0 || isAdHocDisabled}
                    >
                      {i18n._(t`Run command`)}
                    </DropdownItem>
                  ) : (
                    <ToolbarItem>
                      <Tooltip
                        content={i18n._(
                          t`Select an inventory source by clicking the check box beside it.
                          The inventory source can be a single host or a selection of multiple hosts.`
                        )}
                        position="top"
                        key="adhoc"
                      >
                        <Button
                          variant="secondary"
                          aria-label={i18n._(t`Run command`)}
                          onClick={() => setIsAdHocCommandsOpen(true)}
                          isDisabled={hostCount === 0 || isAdHocDisabled}
                        >
                          {i18n._(t`Run command`)}
                        </Button>
                      </Tooltip>
                    </ToolbarItem>
                  )
                }
              </Kebabified>,
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
              key="associate"
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
          optionsRequest={fetchHostsOptions}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Hosts`)}
        />
      )}
      {isAdHocCommandsOpen && (
        <AdHocCommands
          css="margin-right: 20px"
          adHocItems={selected}
          itemId={parseInt(inventoryId, 10)}
          onClose={() => setIsAdHocCommandsOpen(false)}
          credentialTypeId={credentialTypeId}
          moduleOptions={moduleOptions}
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
