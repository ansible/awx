import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Button,
  EmptyState,
  EmptyStateBody,
  EmptyStateIcon,
  Title,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { TeamsAPI, RolesAPI, UsersAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import DataListToolbar from '../../../components/DataListToolbar';
import PaginatedDataList from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';
import TeamRoleListItem from './TeamRoleListItem';
import UserAndTeamAccessAdd from '../../../components/UserAndTeamAccessAdd/UserAndTeamAccessAdd';

const QS_CONFIG = getQSConfig('roles', {
  page: 1,
  page_size: 20,
  order_by: 'id',
});

function TeamRolesList({ i18n, me, team }) {
  const { search } = useLocation();
  const [roleToDisassociate, setRoleToDisassociate] = useState(null);

  const {
    isLoading,
    request: fetchRoles,
    contentError,
    result: {
      roleCount,
      roles,
      isAdminOfOrg,
      relatedSearchableKeys,
      searchableKeys,
    },
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, search);
      const [
        {
          data: { results, count },
        },
        { count: orgAdminCount },
        actionsResponse,
      ] = await Promise.all([
        TeamsAPI.readRoles(team.id, params),
        UsersAPI.readAdminOfOrganizations(me.id, {
          id: team.organization,
        }),
        TeamsAPI.readRoleOptions(team.id),
      ]);
      return {
        roleCount: count,
        roles: results,
        isAdminOfOrg: orgAdminCount > 0,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
      };
    }, [me.id, team.id, team.organization, search]),
    {
      roles: [],
      roleCount: 0,
      isAdminOfOrg: false,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateRole,
    deletionError: disassociationError,
    clearDeletionError: clearDisassociationError,
  } = useDeleteItems(
    useCallback(async () => {
      setRoleToDisassociate(null);
      await RolesAPI.disassociateTeamRole(
        roleToDisassociate.id,
        parseInt(team.id, 10)
      );
    }, [roleToDisassociate, team.id]),
    { qsConfig: QS_CONFIG, fetchItems: fetchRoles }
  );

  const canAdd = team?.summary_fields?.user_capabilities?.edit || isAdminOfOrg;
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

  const isSysAdmin = roles.some(role => role.name === 'System Administrator');
  if (isSysAdmin) {
    return (
      <EmptyState variant="full">
        <EmptyStateIcon icon={CubesIcon} />
        <Title headingLevel="h5" size="lg">
          {i18n._(t`System Administrator`)}
        </Title>
        <EmptyStateBody>
          {i18n._(
            t`System administrators have unrestricted access to all resources.`
          )}
        </EmptyStateBody>
      </EmptyState>
    );
  }

  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
        items={roles}
        itemCount={roleCount}
        pluralizedItemName={i18n._(t`Team Roles`)}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={[
          {
            name: i18n._(t`Role`),
            key: 'role_field__icontains',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`ID`),
            key: 'id',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <UserAndTeamAccessAdd
                      apiModel={TeamsAPI}
                      onFetchData={fetchRoles}
                      title={i18n._(t`Add team permissions`)}
                    />,
                  ]
                : []),
            ]}
          />
        )}
        renderItem={role => (
          <TeamRoleListItem
            key={role.id}
            role={role}
            detailUrl={detailUrl(role)}
            onSelect={item => {
              setRoleToDisassociate(item);
            }}
          />
        )}
      />

      {roleToDisassociate && (
        <AlertModal
          aria-label={i18n._(t`Disassociate role`)}
          isOpen={roleToDisassociate}
          variant="error"
          title={i18n._(t`Disassociate role!`)}
          onClose={() => setRoleToDisassociate(null)}
          actions={[
            <Button
              key="disassociate"
              variant="danger"
              aria-label={i18n._(t`confirm disassociate`)}
              onClick={() => disassociateRole()}
            >
              {i18n._(t`Disassociate`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`Cancel`)}
              onClick={() => setRoleToDisassociate(null)}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          <div>
            {i18n._(
              t`This action will disassociate the following role from ${roleToDisassociate.summary_fields.resource_name}:`
            )}
            <br />
            <strong>{roleToDisassociate.name}</strong>
          </div>
        </AlertModal>
      )}
      {disassociationError && (
        <AlertModal
          isOpen={disassociationError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDisassociationError}
        >
          {i18n._(t`Failed to delete role.`)}
          <ErrorDetail error={disassociationError} />
        </AlertModal>
      )}
    </>
  );
}
export default withI18n()(TeamRolesList);
