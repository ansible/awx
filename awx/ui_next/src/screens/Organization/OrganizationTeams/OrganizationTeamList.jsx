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
    result: { teams, count, relatedSearchableKeys, searchableKeys },
    error,
    isLoading,
    request: fetchTeams,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        OrganizationsAPI.readTeams(id, params),
        OrganizationsAPI.readTeamsOptions(id),
      ]);
      return {
        teams: response.data.results,
        count: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [id, location]),
    {
      teams: [],
      count: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
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
      toolbarSearchableKeys={searchableKeys}
      toolbarRelatedSearchableKeys={relatedSearchableKeys}
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
