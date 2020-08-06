import React, { useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { OrganizationsAPI } from '../../../api';
import PaginatedDataList from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import useRequest from '../../../util/useRequest';
import OrganizationTeamListItem from './OrganizationTeamListItem';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 5,
  order_by: 'name',
});

function OrganizationTeamList({ id, i18n }) {
  const location = useLocation();

  const {
    result: { teams, count },
    error,
    isLoading,
    request: fetchTeams,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const results = await OrganizationsAPI.readTeams(id, params);
      return {
        teams: results.data.results,
        count: results.data.count,
      };
    }, [id, location]),
    {
      teams: [],
      count: 0,
    }
  );

  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);

  return (
    <PaginatedDataList
      contentError={error}
      hasContentLoading={isLoading}
      items={teams}
      itemCount={count}
      pluralizedItemName={i18n._(t`Teams`)}
      qsConfig={QS_CONFIG}
      toolbarSearchColumns={[
        {
          name: i18n._(t`Name`),
          key: 'name__icontains',
          isDefault: true,
        },
        {
          name: i18n._(t`Created by (username)`),
          key: 'created_by__username__icontains',
        },
        {
          name: i18n._(t`Modified by (username)`),
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
        <OrganizationTeamListItem
          key={item.id}
          value={item.name}
          team={item}
          detailUrl={`/teams/${item.id}`}
        />
      )}
    />
  );
}

OrganizationTeamList.propTypes = {
  id: PropTypes.number.isRequired,
};

export { OrganizationTeamList as _OrganizationTeamList };
export default withI18n()(OrganizationTeamList);
