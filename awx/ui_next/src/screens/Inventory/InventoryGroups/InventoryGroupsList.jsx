import React, { useState, useEffect } from 'react';
import { TrashAltIcon } from '@patternfly/react-icons';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '@util/qs';
import { InventoriesAPI, GroupsAPI } from '@api';
import { Button, Tooltip } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';
import DataListToolbar from '@components/DataListToolbar';
import PaginatedDataList, {
  ToolbarAddButton,
} from '@components/PaginatedDataList';
import styled from 'styled-components';
import InventoryGroupItem from './InventoryGroupItem';
import InventoryGroupsDeleteModal from '../shared/InventoryGroupsDeleteModal';

const QS_CONFIG = getQSConfig('group', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

const DeleteButton = styled(Button)`
  padding: 5px 8px;

  &:hover {
    background-color: #d9534f;
    color: white;
  }

  &[disabled] {
    color: var(--pf-c-button--m-plain--Color);
    pointer-events: initial;
    cursor: not-allowed;
  }
`;

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

function InventoryGroupsList({ i18n, location, match }) {
  const [actions, setActions] = useState(null);
  const [contentError, setContentError] = useState(null);
  const [deletionError, setDeletionError] = useState(null);
  const [groupCount, setGroupCount] = useState(0);
  const [groups, setGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selected, setSelected] = useState([]);
  const { isModalOpen, toggleModal } = useModal();

  const inventoryId = match.params.id;
  const fetchGroups = (id, queryString) => {
    const params = parseQueryString(QS_CONFIG, queryString);
    return InventoriesAPI.readGroups(id, params);
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [
          {
            data: { count, results },
          },
          {
            data: { actions: optionActions },
          },
        ] = await Promise.all([
          fetchGroups(inventoryId, location.search),
          InventoriesAPI.readGroupsOptions(inventoryId),
        ]);

        setGroups(results);
        setGroupCount(count);
        setActions(optionActions);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [inventoryId, location]);

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...groups] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

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
    setIsLoading(true);

    try {
      /* eslint-disable no-await-in-loop, no-restricted-syntax */
      /* Delete groups sequentially to avoid api integrity errors */
      for (const group of selected) {
        if (option === 'delete') {
          await GroupsAPI.destroy(+group.id);
        } else if (option === 'promote') {
          await InventoriesAPI.promoteGroup(inventoryId, +group.id);
        }
      }
      /* eslint-enable no-await-in-loop, no-restricted-syntax */
    } catch (error) {
      setDeletionError(error);
    }

    toggleModal();

    try {
      const {
        data: { count, results },
      } = await fetchGroups(inventoryId, location.search);
      setGroups(results);
      setGroupCount(count);
    } catch (error) {
      setContentError(error);
    }

    setIsLoading(false);
  };

  const canAdd =
    actions && Object.prototype.hasOwnProperty.call(actions, 'POST');
  const isAllSelected =
    selected.length > 0 && selected.length === groups.length;

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading}
        items={groups}
        itemCount={groupCount}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'name',
            isDefault: true,
          },
          {
            name: i18n._(t`Group Type`),
            key: 'parents__isnull',
            isBoolean: true,
            booleanLabels: {
              true: i18n._(t`Show Only Root Groups`),
              false: i18n._(t`Show All Groups`),
            },
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
            onSelectAll={handleSelectAll}
            qsConfig={QS_CONFIG}
            additionalControls={[
              <Tooltip content={renderTooltip()} position="top" key="delete">
                <div>
                  <DeleteButton
                    variant="plain"
                    aria-label={i18n._(t`Delete`)}
                    onClick={toggleModal}
                    isDisabled={
                      selected.length === 0 || selected.some(cannotDelete)
                    }
                  >
                    <TrashAltIcon />
                  </DeleteButton>
                </div>
              </Tooltip>,
              canAdd && (
                <ToolbarAddButton
                  key="add"
                  linkTo={`/inventories/inventory/${inventoryId}/groups/add`}
                />
              ),
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
          variant="danger"
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
export default withI18n()(withRouter(InventoryGroupsList));
