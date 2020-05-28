import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

import { getQSConfig, parseQueryString } from '../../../util/qs';
import { UsersAPI } from '../../../api';
import useRequest from '../../../util/useRequest';
import PaginatedDataList from '../../../components/PaginatedDataList';
import DatalistToolbar from '../../../components/DataListToolbar';
import UserAccessListItem from './UserAccessListItem';
import UserAndTeamAccessAdd from '../../../components/UserAndTeamAccessAdd/UserAndTeamAccessAdd';

const QS_CONFIG = getQSConfig('roles', {
  page: 1,
  page_size: 20,
  order_by: 'id',
});
// TODO Figure out how to best conduct a search of this list.
// Since we only have a role ID in the top level of each role object
// we can't really search using the normal search parameters.
function UserAccessList({ i18n }) {
  const { id } = useParams();
  const { search } = useLocation();
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  const {
    isLoading,
    request: fetchRoles,
    error,
    result: { roleCount, roles, options },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);
      const [
        {
          data: { results, count },
        },
        {
          data: { actions },
        },
      ] = await Promise.all([
        UsersAPI.readRoles(id, params),
        UsersAPI.readRoleOptions(id),
      ]);
      return { roleCount: count, roles: results, options: actions };
    }, [id, search]),
    {
      roles: [],
      roleCount: 0,
    }
  );
  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);
  const canAdd =
    options && Object.prototype.hasOwnProperty.call(options, 'POST');

  const saveRoles = () => {
    setIsWizardOpen(false);
    fetchRoles();
  };

  const detailUrl = role => {
    const { resource_id, resource_type } = role.summary_fields;

    if (!role || !resource_type) {
      return null;
    }

    if (resource_type?.includes('template')) {
      return `/templates/${resource_type}/${resource_id}/details`;
    }
    if (resource_type?.includes('inventory')) {
      return `/inventories/${resource_type}/${resource_id}/details`;
    }
    return `/${resource_type}s/${resource_id}/details`;
  };

  return (
    <>
      <PaginatedDataList
        contentError={error}
        hasContentLoading={isLoading}
        items={roles}
        itemCount={roleCount}
        pluralizedItemName={i18n._(t`User Roles`)}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Role`),
            key: 'role_field',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`Name`),
            key: 'id',
          },
        ]}
        renderItem={role => {
          return (
            <UserAccessListItem
              key={role.id}
              value={role.name}
              role={role}
              detailUrl={detailUrl(role)}
              onSelect={() => {}}
              isSelected={false}
            />
          );
        }}
        renderToolbar={props => (
          <DatalistToolbar
            {...props}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <Button
                      key="add"
                      aria-label={i18n._(t`Add resource roles`)}
                      onClick={() => {
                        setIsWizardOpen(true);
                      }}
                    >
                      Add
                    </Button>,
                  ]
                : []),
            ]}
          />
        )}
      />
      {isWizardOpen && (
        <UserAndTeamAccessAdd
          apiModel={UsersAPI}
          isOpen={isWizardOpen}
          onSave={saveRoles}
          onClose={() => setIsWizardOpen(false)}
          title={i18n._(t`Add user permissions`)}
        />
      )}
    </>
  );
}
export default withI18n()(UserAccessList);
