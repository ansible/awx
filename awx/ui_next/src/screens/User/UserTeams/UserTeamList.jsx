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
    result: { teams, count },
    error: contentError,
    isLoading,
    request: fetchOrgs,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const {
        data: { results, count: teamCount },
      } = await UsersAPI.readTeams(userId, params);
      return {
        teams: results,
        count: teamCount,
      };
    }, [userId, location.search]),
    {
      teams: [],
      count: 0,
    }
  );

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

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
          key: 'name',
          isDefault: true,
        },
        {
          name: i18n._(t`Organization`),
          key: 'organization__name',
        },
      ]}
    />
  );
}

export default withI18n()(UserTeamList);
