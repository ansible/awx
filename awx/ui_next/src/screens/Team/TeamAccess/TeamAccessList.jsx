import React, { useCallback, useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Button } from '@patternfly/react-core';
import { TeamsAPI } from '../../../api';

import useRequest from '../../../util/useRequest';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import TeamAccessListItem from './TeamAccessListItem';
import UserAndTeamAccessAdd from '../../../components/UserAccessAdd/UserAndTeamAccessAdd';

const QS_CONFIG = getQSConfig('team', {
  page: 1,
  page_size: 20,
  order_by: 'id',
});

function TeamAccessList({ i18n }) {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const { search } = useLocation();
  const { id } = useParams();

  const {
    isLoading,
    request: fetchRoles,
    contentError,
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
        TeamsAPI.readRoles(id, params),
        TeamsAPI.readRoleOptions(id),
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

  const saveRoles = () => {
    setIsWizardOpen(false);
    fetchRoles();
  };

  const canAdd =
    options && Object.prototype.hasOwnProperty.call(options, 'POST');

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
        contentError={contentError}
        hasContentLoading={isLoading}
        items={roles}
        itemCount={roleCount}
        pluralizedItemName={i18n._(t`Teams`)}
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
        renderToolbar={props => (
          <DataListToolbar
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
        renderItem={role => (
          <TeamAccessListItem
            key={role.id}
            role={role}
            detailUrl={detailUrl(role)}
            onSelect={() => {}}
          />
        )}
      />
      {isWizardOpen && (
        <UserAndTeamAccessAdd
          apiModel={TeamsAPI}
          isOpen={isWizardOpen}
          onSave={saveRoles}
          onClose={() => setIsWizardOpen(false)}
          title={i18n._(t`Add team permissions`)}
        />
      )}
    </>
  );
}
export default withI18n()(TeamAccessList);
