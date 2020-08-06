import React, { useCallback, useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, Tooltip } from '@patternfly/react-core';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useSelected from '../../../util/useSelected';
import useRequest from '../../../util/useRequest';
import { InventoriesAPI, GroupsAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import InventoryGroupItem from './InventoryGroupItem';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

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
  const location = useLocation();
  const { isModalOpen, toggleModal } = useModal();
  const { id: inventoryId } = useParams();

  const {
    result: { groups, groupCount, actions },
    error: contentError,
    isLoading,
    request: fetchGroups,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        InventoriesAPI.readGroups(inventoryId, params),
        InventoriesAPI.readGroupsOptions(inventoryId),
      ]);
      return {
        groups: response.data.results,
        groupCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [inventoryId, location]),
    {
      groups: [],
      groupCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

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
    fetchGroups();
    setSelected([]);
    setIsDeleteLoading(false);
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');

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
              <Tooltip content={renderTooltip()} position="top" key="delete">
                <div>
                  <Button
                    variant="danger"
                    aria-label={i18n._(t`Delete`)}
                    onClick={toggleModal}
                    isDisabled={
                      selected.length === 0 || selected.some(cannotDelete)
                    }
                  >
                    {i18n._(t`Delete`)}
                  </Button>
                </div>
              </Tooltip>,
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
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
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
