import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { useLocation, useParams } from 'react-router-dom';
import { t } from '@lingui/macro';

import PaginatedDataList from '../../../components/PaginatedDataList';
import useRequest from '../../../util/useRequest';
import { UsersAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import UserTeamListItem from './UserTeamListItem';

const QS_CONFIG = getQSConfig('teams', {
  page: 1,
  page_size: 20,
  order_by: 'name',
});

function UserTeamList({ i18n }) {
  const location = useLocation();
  const { id: userId } = useParams();

  const {
    result: { teams, count, actions, relatedSearchFields },
    error: contentError,
    isLoading,
    request: fetchOrgs,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [
        {
          data: { results, count: teamCount },
        },
        actionsResponse,
      ] = await Promise.all([
        UsersAPI.readTeams(userId, params),
        UsersAPI.readTeamsOptions(userId),
      ]);
      return {
        teams: results,
        count: teamCount,
        actions: actionsResponse.data.actions,
        relatedSearchFields: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
      };
    }, [userId, location.search]),
    {
      teams: [],
      count: 0,
      actions: {},
      relatedSearchFields: [],
    }
  );

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  const relatedSearchableKeys = relatedSearchFields || [];
  const searchableKeys = Object.keys(actions?.GET || {}).filter(
    key => actions.GET[key].filterable
  );

  return (
    <PaginatedDataList
      items={teams}
      contentError={contentError}
      hasContentLoading={isLoading}
      itemCount={count}
      pluralizedItemName={i18n._(t`Teams`)}
      qsConfig={QS_CONFIG}
      renderItem={team => (
        <UserTeamListItem
          key={team.id}
          value={team.name}
          team={team}
          detailUrl={`/teams/${team.id}/details`}
          onSelect={() => {}}
          isSelected={false}
        />
      )}
      toolbarSearchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Organization`),
          key: 'organization__name__icontains',
        },
      ]}
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
    />
  );
}

export default withI18n()(UserTeamList);
