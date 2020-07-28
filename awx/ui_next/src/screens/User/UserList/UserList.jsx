import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useRouteMatch } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Card, PageSection } from '@patternfly/react-core';
import { UsersAPI } from '../../../api';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import UserListItem from './UserListItem';

const QS_CONFIG = getQSConfig('user', {
  page: 1,
  page_size: 20,
  order_by: 'username',
});

function UserList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();
  const [selected, setSelected] = useState([]);

  const {
    result: { users, itemCount, actions },
    error: contentError,
    isLoading,
    request: fetchUsers,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        UsersAPI.read(params),
        UsersAPI.readOptions(),
      ]);
      return {
        users: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [location]),
    {
      users: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const isAllSelected = selected.length === users.length && selected.length > 0;

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteUsers,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(selected.map(user => UsersAPI.destroy(user.id)));
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchUsers,
    }
  );

  const handleUserDelete = async () => {
    await deleteUsers();
    setSelected([]);
  };

  const hasContentLoading = isDeleteLoading || isLoading;
  const canAdd = actions && actions.POST;

  const handleSelectAll = isSelected => {
    setSelected(isSelected ? [...users] : []);
  };

  const handleSelect = row => {
    if (selected.some(s => s.id === row.id)) {
      setSelected(selected.filter(s => s.id !== row.id));
    } else {
      setSelected(selected.concat(row));
    }
  };

  return (
    <>
      <PageSection>
        <Card>
          <PaginatedDataList
            contentError={contentError}
            hasContentLoading={hasContentLoading}
            items={users}
            itemCount={itemCount}
            pluralizedItemName={i18n._(t`Users`)}
            qsConfig={QS_CONFIG}
            onRowClick={handleSelect}
            toolbarSearchColumns={[
              {
                name: i18n._(t`Username`),
                key: 'username',
                isDefault: true,
              },
              {
                name: i18n._(t`First Name`),
                key: 'first_name',
              },
              {
                name: i18n._(t`Last Name`),
                key: 'last_name',
              },
            ]}
            toolbarSortColumns={[
              {
                name: i18n._(t`Username`),
                key: 'username',
              },
              {
                name: i18n._(t`First Name`),
                key: 'first_name',
              },
              {
                name: i18n._(t`Last Name`),
                key: 'last_name',
              },
            ]}
            renderToolbar={props => (
              <DataListToolbar
                {...props}
                showSelectAll
                isAllSelected={isAllSelected}
                onSelectAll={handleSelectAll}
                qsConfig={QS_CONFIG}
                additionalControls={[
                  ...(canAdd
                    ? [
                        <ToolbarAddButton
                          key="add"
                          linkTo={`${match.url}/add`}
                        />,
                      ]
                    : []),
                  <ToolbarDeleteButton
                    key="delete"
                    onDelete={handleUserDelete}
                    itemsToDelete={selected}
                    pluralizedItemName="Users"
                  />,
                ]}
              />
            )}
            renderItem={o => (
              <UserListItem
                key={o.id}
                user={o}
                detailUrl={`${match.url}/${o.id}/details`}
                isSelected={selected.some(row => row.id === o.id)}
                onSelect={() => handleSelect(o)}
              />
            )}
            emptyStateControls={
              canAdd ? (
                <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
              ) : null
            }
          />
        </Card>
      </PageSection>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more users.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(UserList);
