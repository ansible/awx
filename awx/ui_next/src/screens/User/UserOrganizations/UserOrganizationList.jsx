import React, { useCallback, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { t } from '@lingui/macro';

import PaginatedTable, {
  HeaderRow,
  HeaderCell,
} from '../../../components/PaginatedTable';
import useRequest from '../../../util/useRequest';
import { UsersAPI } from '../../../api';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import UserOrganizationListItem from './UserOrganizationListItem';

const QS_CONFIG = getQSConfig('organizations', {
  page: 1,
  page_size: 20,
  order_by: 'name',
  type: 'organization',
});

function UserOrganizationList() {
  const location = useLocation();
  const { id: userId } = useParams();

  const {
    result: { organizations, count },
    error: contentError,
    isLoading,
    request: fetchOrgs,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const {
        data: { results, count: orgCount },
      } = await UsersAPI.readOrganizations(userId, params);
      return {
        organizations: results,
        count: orgCount,
      };
    }, [userId, location.search]),
    {
      organizations: [],
      count: 0,
    }
  );

  useEffect(() => {
    fetchOrgs();
  }, [fetchOrgs]);

  return (
    <PaginatedTable
      items={organizations}
      contentError={contentError}
      hasContentLoading={isLoading}
      itemCount={count}
      pluralizedItemName={t`Organizations`}
      qsConfig={QS_CONFIG}
      toolbarSearchColumns={[
        { name: t`Name`, key: 'name__icontains', isDefault: true },
      ]}
      headerRow={
        <HeaderRow qsConfig={QS_CONFIG} isSelectable={false}>
          <HeaderCell sortKey="name">{t`Name`}</HeaderCell>
          <HeaderCell>{t`Description`}</HeaderCell>
        </HeaderRow>
      }
      renderRow={(organization, index) => (
        <UserOrganizationListItem
          key={organization.id}
          value={organization.name}
          organization={organization}
          detailUrl={`/organizations/${organization.id}/details`}
          onSelect={() => {}}
          isSelected={false}
          rowIndex={index}
        />
      )}
    />
  );
}

export default UserOrganizationList;
