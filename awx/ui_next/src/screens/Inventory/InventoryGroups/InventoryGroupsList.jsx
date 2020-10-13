import React, { useCallback, useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Button,
  Tooltip,
  DropdownItem,
  ToolbarGroup,
  ToolbarItem,
} from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useSelected from '../../../util/useSelected';
import useRequest from '../../../util/useRequest';
import { InventoriesAPI, GroupsAPI, CredentialTypesAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';

import InventoryGroupItem from './InventoryGroupItem';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

import AdHocCommands from '../../../components/AdHocCommands/AdHocCommands';
import { Kebabified } from '../../../contexts/Kebabified';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function cannotDelete(item) {
  return !item.summary_fields.user_capabilities.delete;
}

const useModal = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  function toggleModal() {
    setIsModalOpen(!isModalOpen);
  }

  return {
    isModalOpen,
    toggleModal,
  };
};

function InventoryGroupsList({ i18n }) {
  const [deletionError, setDeletionError] = useState(null);
  const [isDeleteLoading, setIsDeleteLoading] = useState(false);
  const [isAdHocCommandsOpen, setIsAdHocCommandsOpen] = useState(false);
  const location = useLocation();
  const { isModalOpen, toggleModal } = useModal();
  const { id: inventoryId } = useParams();

  const {
    result: {
      groups,
      groupCount,
      actions,
      relatedSearchableKeys,
      searchableKeys,
      moduleOptions,
      credentialTypeId,
      isAdHocDisabled,
    },
    error: contentError,
    isLoading,
    request: fetchData,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, groupOptions, adHocOptions, cred] = await Promise.all([
        InventoriesAPI.readGroups(inventoryId, params),
        InventoriesAPI.readGroupsOptions(inventoryId),
        InventoriesAPI.readAdHocOptions(inventoryId),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
      ]);

      return {
        groups: response.data.results,
        groupCount: response.data.count,
        actions: groupOptions.data.actions,
        relatedSearchableKeys: (
          groupOptions?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          groupOptions.data.actions?.GET || {}
        ).filter(key => groupOptions.data.actions?.GET[key].filterable),
        moduleOptions: adHocOptions.data.actions.GET.module_name.choices,
        credentialTypeId: cred.data.results[0].id,
        isAdHocDisabled: !adHocOptions.data.actions.POST,
      };
    }, [inventoryId, location]),
    {
      groups: [],
      groupCount: 0,
      actions: {},
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    groups
  );

  const renderTooltip = () => {
    const itemsUnableToDelete = selected
      .filter(cannotDelete)
      .map(item => item.name)
      .join(', ');

    if (selected.some(cannotDelete)) {
      return (
        <div>
          {i18n._(
            t`You do not have permission to delete the following Groups: ${itemsUnableToDelete}`
          )}
        </div>
      );
    }
    if (selected.length) {
      return i18n._(t`Delete`);
    }
    return i18n._(t`Select a row to delete`);
  };

  const handleDelete = async option => {
    setIsDeleteLoading(true);

    try {
      /* eslint-disable no-await-in-loop */
      /* Delete groups sequentially to avoid api integrity errors */
      /* https://eslint.org/docs/rules/no-await-in-loop#when-not-to-use-it */
      for (let i = 0; i < selected.length; i++) {
        const group = selected[i];
        if (option === 'delete') {
          await GroupsAPI.destroy(+group.id);
        } else if (option === 'promote') {
          await InventoriesAPI.promoteGroup(inventoryId, +group.id);
        }
      }
      /* eslint-enable no-await-in-loop */
    } catch (error) {
      setDeletionError(error);
    }

    toggleModal();
    fetchData();
    setSelected([]);
    setIsDeleteLoading(false);
  };
  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const kebabedAdditionalControls = () => {
    return (
      <>
        <DropdownItem
          key="run command"
          onClick={() => setIsAdHocCommandsOpen(true)}
          isDisabled={groupCount === 0 || isAdHocDisabled}
        >
          {i18n._(t`Run command`)}
        </DropdownItem>

        <DropdownItem
          variant="danger"
          aria-label={i18n._(t`Delete`)}
          key="delete"
          onClick={toggleModal}
          isDisabled={selected.length === 0 || selected.some(cannotDelete)}
        >
          {i18n._(t`Delete`)}
        </DropdownItem>
      </>
    );
  };

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDeleteLoading}
        items={groups}
        itemCount={groupCount}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name__icontains',
            isDefault: true,
          },
          {
            name: i18n._(t`Group type`),
            key: 'parents__isnull',
            isBoolean: true,
            booleanLabels: {
              true: i18n._(t`Show only root groups`),
              false: i18n._(t`Show all groups`),
            },
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
          <InventoryGroupItem
            key={item.id}
            group={item}
            inventoryId={inventoryId}
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
                      linkTo={`/inventories/inventory/${inventoryId}/groups/add`}
                    />,
                  ]
                : []),
              <Kebabified>
                {({ isKebabified }) => (
                  <>
                    {isKebabified ? (
                      kebabedAdditionalControls()
                    ) : (
                      <ToolbarGroup>
                        <ToolbarItem>
                          <Tooltip
                            content={i18n._(
                              t`Select an inventory source by clicking the check box beside it. The inventory source can be a single group or a selection of multiple groups.`
                            )}
                            position="top"
                            key="adhoc"
                          >
                            <Button
                              variant="secondary"
                              aria-label={i18n._(t`Run command`)}
                              onClick={() => setIsAdHocCommandsOpen(true)}
                              isDisabled={groupCount === 0 || isAdHocDisabled}
                            >
                              {i18n._(t`Run command`)}
                            </Button>
                          </Tooltip>
                        </ToolbarItem>
                        <ToolbarItem>
                          <Tooltip
                            content={renderTooltip()}
                            position="top"
                            key="delete"
                          >
                            <div>
                              <Button
                                variant="danger"
                                aria-label={i18n._(t`Delete`)}
                                onClick={toggleModal}
                                isDisabled={
                                  selected.length === 0 ||
                                  selected.some(cannotDelete)
                                }
                              >
                                {i18n._(t`Delete`)}
                              </Button>
                            </div>
                          </Tooltip>
                        </ToolbarItem>
                      </ToolbarGroup>
                    )}
                  </>
                )}
              </Kebabified>,
            ]}
          />
        )}
        emptyStateControls={
          canAdd && (
            <ToolbarAddButton
              key="add"
              linkTo={`/inventories/inventory/${inventoryId}/groups/add`}
            />
          )
        }
      />
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
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          aria-label={i18n._(t`deletion error`)}
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete one or more groups.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
      <InventoryGroupsDeleteModal
        groups={selected}
        isModalOpen={isModalOpen}
        onClose={toggleModal}
        onDelete={handleDelete}
      />
    </>
  );
}
export default withI18n()(InventoryGroupsList);
