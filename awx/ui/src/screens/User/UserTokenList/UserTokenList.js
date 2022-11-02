import React, { useCallback, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from 'util/qs';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  ToolbarDeleteButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import useSelected from 'hooks/useSelected';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import { UsersAPI, TokensAPI } from 'api';
import DataListToolbar from 'components/DataListToolbar';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import UserTokensListItem from './UserTokenListItem';

const QS_CONFIG = getQSConfig('user', {
  page: 1,
  page_size: 20,
  order_by: 'application__name',
});
function UserTokenList() {
  const location = useLocation();
  const { id } = useParams();

  const {
    error,
    isLoading,
    request: fetchTokens,
    result: { tokens, itemCount, relatedSearchableKeys, searchableKeys },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        {
          data: { results, count },
        },
        actionsResponse,
      ] = await Promise.all([
        UsersAPI.readTokens(id, params),
        UsersAPI.readTokenOptions(id),
      ]);
      const modifiedResults = results.map((result) => {
        result.summary_fields = {
          user: result.summary_fields.user,
          application: result.summary_fields.application,
          user_capabilities: { delete: true },
        };
        result.name = result.summary_fields.application?.name;
        return result;
      });
      return {
        tokens: modifiedResults,
        itemCount: count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
      };
    }, [id, location.search]),
    { tokens: [], itemCount: 0, relatedSearchableKeys: [], searchableKeys: [] }
  );

  useEffect(() => {
    fetchTokens();
  }, [fetchTokens]);

  const { selected, isAllSelected, handleSelect, clearSelected, selectAll } =
    useSelected(tokens);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTokens,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(
      () =>
        Promise.all(
          selected.map(({ id: tokenId }) => TokensAPI.destroy(tokenId))
        ),
      [selected]
    ),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTokens,
    }
  );
  const handleDelete = async () => {
    await deleteTokens();
    clearSelected();
  };

  const canAdd = true;

  const modifiedSelected = selected.map((item) => {
    if (item.application === null) {
      return {
        ...item,
        name: t`Personal Access Token`,
      };
    }
    return item;
  });

  return (
    <>
      <PaginatedTable
        contentError={error}
        hasContentLoading={isLoading || isDeleteLoading}
        items={tokens}
        itemCount={itemCount}
        pluralizedItemName={t`Tokens`}
        qsConfig={QS_CONFIG}
        clearSelected={clearSelected}
        toolbarSearchColumns={[
          {
            name: t`Application name`,
            key: 'application__name__icontains',
            isDefault: true,
          },
          {
            name: t`Description`,
            key: 'description__icontains',
          },
        ]}
        toolbarSortColumns={[
          {
            name: t`Application name`,
            key: 'application__name',
          },
          {
            name: t`Description`,
            key: 'description',
          },
          {
            name: t`Scope`,
            key: 'scope',
          },
          {
            name: t`Expires`,
            key: 'expires',
          },
          {
            name: t`Created`,
            key: 'created',
          },
          {
            name: t`Modified`,
            key: 'modified',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            isAllSelected={isAllSelected}
            qsConfig={QS_CONFIG}
            onSelectAll={selectAll}
            additionalControls={[
              ...(canAdd
                ? [
                    <ToolbarAddButton
                      key="add"
                      linkTo={`${location.pathname}/add`}
                    />,
                  ]
                : []),
              <ToolbarDeleteButton
                ouiaId="user-token-delete-button"
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={modifiedSelected}
                pluralizedItemName={t`User tokens`}
              />,
            ]}
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG}>
            <HeaderCell sortKey="application__name">{t`Application Name`}</HeaderCell>
            <HeaderCell sortKey="description">{t`Description`}</HeaderCell>
            <HeaderCell sortKey="scope">{t`Scope`}</HeaderCell>
            <HeaderCell sortKey="expires">{t`Expires`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(token, index) => (
          <UserTokensListItem
            key={token.id}
            token={token}
            onSelect={() => {
              handleSelect(token);
            }}
            isSelected={selected.some((row) => row.id === token.id)}
            rowIndex={index}
          />
        )}
        emptyStateControls={
          canAdd ? (
            <ToolbarAddButton key="add" linkTo={`${location.pathname}/add`} />
          ) : null
        }
      />
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete one or more user tokens.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

export default UserTokenList;
