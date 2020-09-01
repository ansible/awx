import React, { useCallback, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import PaginatedDataList, {
  ToolbarAddButton,
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import useSelected from '../../../util/useSelected';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import { UsersAPI, TokensAPI } from '../../../api';
import DataListToolbar from '../../../components/DataListToolbar';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';
import UserTokensListItem from './UserTokenListItem';

const QS_CONFIG = getQSConfig('user', {
  page: 1,
  page_size: 20,
  order_by: 'application__name',
});
function UserTokenList({ i18n }) {
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
      const modifiedResults = results.map(result => {
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
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [id, location.search]),
    { tokens: [], itemCount: 0, relatedSearchableKeys: [], searchableKeys: [] }
  );

  useEffect(() => {
    fetchTokens();
  }, [fetchTokens]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    tokens
  );

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteTokens,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      return Promise.all(
        selected.map(({ id: tokenId }) => TokensAPI.destroy(tokenId))
      );
    }, [selected]),
    {
      qsConfig: QS_CONFIG,
      allItemsSelected: isAllSelected,
      fetchItems: fetchTokens,
    }
  );
  const handleDelete = async () => {
    await deleteTokens();
    setSelected([]);
  };

  const canAdd = true;

  return (
    <>
      <PaginatedDataList
        contentError={error}
        hasContentLoading={isLoading || isDeleteLoading}
        items={tokens}
        itemCount={itemCount}
        pluralizedItemName={i18n._(t`Tokens`)}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'application__name__icontains',
            isDefault: true,
          },
          {
            name: i18n._(t`Description`),
            key: 'description__icontains',
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'application__name',
          },
          {
            name: i18n._(t`Scope`),
            key: 'scope',
          },
          {
            name: i18n._(t`Expires`),
            key: 'expires',
          },
          {
            name: i18n._(t`Created`),
            key: 'created',
          },
          {
            name: i18n._(t`Modified`),
            key: 'modified',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            showSelectAll
            isAllSelected={isAllSelected}
            qsConfig={QS_CONFIG}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...tokens] : [])
            }
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
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={selected}
                pluralizedItemName={i18n._(t`User tokens`)}
              />,
            ]}
          />
        )}
        renderItem={token => (
          <UserTokensListItem
            key={token.id}
            token={token}
            onSelect={() => {
              handleSelect(token);
            }}
            isSelected={selected.some(row => row.id === token.id)}
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
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete one or more user tokens.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(UserTokenList);
