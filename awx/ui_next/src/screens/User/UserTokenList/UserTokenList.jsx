import React, { useCallback, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import useSelected from '../../../util/useSelected';
import useRequest from '../../../util/useRequest';
import { UsersAPI } from '../../../api';
import DataListToolbar from '../../../components/DataListToolbar';
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
    result: { tokens, itemCount },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const {
        data: { results, count },
      } = await UsersAPI.readTokens(id, params);
      const modifiedResults = results.map(result => {
        result.summary_fields = {
          user: result.summary_fields.user,
          application: result.summary_fields.application,
          user_capabilities: { delete: true },
        };
        result.name = result.summary_fields.application?.name;
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

  const canAdd = true;
  return (
    <PaginatedDataList
      contentError={error}
      hasContentLoading={isLoading}
      items={tokens}
      itemCount={itemCount}
      pluralizedItemName={i18n._(t`Tokens`)}
      qsConfig={QS_CONFIG}
      onRowClick={handleSelect}
      toolbarSearchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'application__name',
          isDefault: true,
        },
        {
          name: i18n._(t`Description`),
          key: 'description',
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
      renderToolbar={props => (
        <DataListToolbar
          {...props}
          showSelectAll
          isAllSelected={isAllSelected}
          qsConfig={QS_CONFIG}
          onSelectAll={isSelected => setSelected(isSelected ? [...tokens] : [])}
          additionalControls={[
            ...(canAdd
              ? [
                  <ToolbarAddButton
                    key="add"
                    linkTo={`${location.pathname}/add`}
                  />,
                ]
              : []),
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
  );
}

export default withI18n()(UserTokenList);
