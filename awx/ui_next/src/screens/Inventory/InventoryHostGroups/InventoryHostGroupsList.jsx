import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Tooltip,
  DropdownItem,
  ToolbarItem,
} from '@patternfly/react-core';
import { getQSConfig, parseQueryString, mergeParams } from '../../../util/qs';
import useRequest, {
  useDismissableError,
  useDeleteItems,
} from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import { HostsAPI, InventoriesAPI, CredentialTypesAPI } from '../../../api';
import DataListToolbar from '../../../components/DataListToolbar';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import AssociateModal from '../../../components/AssociateModal';
import DisassociateButton from '../../../components/DisassociateButton';
import { Kebabified } from '../../../contexts/Kebabified';
import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import InventoryHostGroupItem from './InventoryHostGroupItem';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function InventoryHostGroupsList({ i18n }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAdHocCommandsOpen, setIsAdHocCommandsOpen] = useState(false);
  const { hostId, id: invId } = useParams();
  const { search } = useLocation();

  const {
    result: {
      groups,
      itemCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
      moduleOptions,
      isAdHocDisabled,
      credentialTypeId,
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
        adHocOptions,
        cred,
      ] = await Promise.all([
        HostsAPI.readAllGroups(hostId, params),
        HostsAPI.readGroupsOptions(hostId),
        InventoriesAPI.readAdHocOptions(invId),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
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
        moduleOptions: adHocOptions.data.actions.GET.module_name.choices,
        credentialTypeId: cred.data.results[0].id,
        isAdHocDisabled: !adHocOptions.data.actions.POST,
      };
    }, [hostId, search]), // eslint-disable-line react-hooks/exhaustive-deps
    {
      groups: [],
      itemCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
      moduleOptions: [],
      isAdHocDisabled: true,
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
              <Kebabified>
                {({ isKebabified }) =>
                  isKebabified ? (
                    <DropdownItem
                      key="run command"
                      aria-label={i18n._(t`Run command`)}
                      onClick={() => setIsAdHocCommandsOpen(true)}
                      isDisabled={itemCount === 0 || isAdHocDisabled}
                    >
                      {i18n._(t`Run command`)}
                    </DropdownItem>
                  ) : (
                    <ToolbarItem>
                      <Tooltip
                        content={i18n._(
                          t`Select an inventory source by clicking the check box beside it. The inventory source can be a single group or host, a selection of multiple hosts, or a selection of multiple groups.`
                        )}
                        position="top"
                        key="adhoc"
                      >
                        <Button
                          key="run command"
                          variant="secondary"
                          aria-label={i18n._(t`Run command`)}
                          onClick={() => setIsAdHocCommandsOpen(true)}
                          isDisabled={itemCount === 0 || isAdHocDisabled}
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
          optionsRequest={fetchGroupsOptions}
          isModalOpen={isModalOpen}
          onAssociate={handleAssociate}
          onClose={() => setIsModalOpen(false)}
          title={i18n._(t`Select Groups`)}
        />
      )}
      {isAdHocCommandsOpen && (
        <AdHocCommands
          css="margin-right: 20px"
          adHocItems={selected}
          itemId={parseInt(invId, 10)}
          onClose={() => setIsAdHocCommandsOpen(false)}
          credentialTypeId={credentialTypeId}
          moduleOptions={moduleOptions}
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
