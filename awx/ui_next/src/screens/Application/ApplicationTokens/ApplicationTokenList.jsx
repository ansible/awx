import React, { useCallback, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import PaginatedDataList, {
  ToolbarDeleteButton,
} from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { TokensAPI, ApplicationsAPI } from '../../../api';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import useSelected from '../../../util/useSelected';
import ApplicationTokenListItem from './ApplicationTokenListItem';
import DatalistToolbar from '../../../components/DataListToolbar';

const QS_CONFIG = getQSConfig('applications', {
  page: 1,
  page_size: 20,
  order_by: 'user__username',
});

function ApplicationTokenList({ i18n }) {
  const { id } = useParams();
  const location = useLocation();
  const {
    error,
    isLoading,
    result: { tokens, itemCount },
    request: fetchTokens,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const {
        data: { results, count },
      } = await ApplicationsAPI.readTokens(id, params);
      const modifiedResults = results.map(result => {
        result.summary_fields = {
          user: result.summary_fields.user,
          application: result.summary_fields.application,
          user_capabilities: { delete: true },
        };
        result.name = result.summary_fields.user?.username;
        return result;
      });
      return { tokens: modifiedResults, itemCount: count };
    }, [id, location.search]),
    { tokens: [], itemCount: 0 }
  );

  useEffect(() => {
    fetchTokens();
  }, [fetchTokens]);

  const { selected, isAllSelected, handleSelect, setSelected } = useSelected(
    tokens
  );
  const {
    isLoading: deleteLoading,
    deletionError,
    deleteItems: handleDeleteApplications,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      await Promise.all(
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
    await handleDeleteApplications();
    setSelected([]);
  };
  return (
    <>
      <PaginatedDataList
        contentError={error}
        hasContentLoading={isLoading || deleteLoading}
        items={tokens}
        itemCount={itemCount}
        pluralizedItemName={i18n._(t`Tokens`)}
        qsConfig={QS_CONFIG}
        onRowClick={handleSelect}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Name`),
            key: 'user__username',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'user__username',
          },
          {
            name: i18n._(t`Scope`),
            key: 'scope',
          },
          {
            name: i18n._(t`Expiration`),
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
        renderToolbar={props => (
          <DatalistToolbar
            {...props}
            showSelectAll
            showExpandCollapse
            isAllSelected={isAllSelected}
            onSelectAll={isSelected =>
              setSelected(isSelected ? [...tokens] : [])
            }
            qsConfig={QS_CONFIG}
            additionalControls={[
              <ToolbarDeleteButton
                key="delete"
                onDelete={handleDelete}
                itemsToDelete={selected}
                pluralizedItemName={i18n._(t`Tokens`)}
              />,
            ]}
          />
        )}
        renderItem={token => (
          <ApplicationTokenListItem
            key={token.id}
            value={token.name}
            token={token}
            detailUrl={`/users/${token.summary_fields.user.id}/details`}
            onSelect={() => handleSelect(token)}
            isSelected={selected.some(row => row.id === token.id)}
          />
        )}
      />
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to delete one or more tokens.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(ApplicationTokenList);
