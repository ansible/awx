import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Button,
  EmptyState,
  EmptyStateBody,
  EmptyStateIcon,
  Title,
} from '@patternfly/react-core';
import { CubesIcon } from '@patternfly/react-icons';
import { TeamsAPI, RolesAPI, UsersAPI } from 'api';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import DataListToolbar from 'components/DataListToolbar';
import PaginatedTable, {
  HeaderCell,
  HeaderRow,
  ToolbarAddButton,
  getSearchableKeys,
} from 'components/PaginatedTable';
import { getQSConfig, parseQueryString } from 'util/qs';
import ErrorDetail from 'components/ErrorDetail';
import AlertModal from 'components/AlertModal';
import UserAndTeamAccessAdd from 'components/UserAndTeamAccessAdd/UserAndTeamAccessAdd';
import TeamRoleListItem from './TeamRoleListItem';

const QS_CONFIG = getQSConfig('roles', {
  page: 1,
  page_size: 20,
  order_by: 'id',
});

function TeamRolesList({ me, team }) {
  const { search } = useLocation();
  const [roleToDisassociate, setRoleToDisassociate] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [associateError, setAssociateError] = useState(null);

  const {
    isLoading,
    request: fetchRoles,
    error: contentError,
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
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
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
  const detailUrl = (role) => {
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

  const isSysAdmin = roles.some((role) => role.name === 'System Administrator');
  if (isSysAdmin) {
    return (
      <EmptyState variant="full">
        <EmptyStateIcon icon={CubesIcon} />
        <Title headingLevel="h5" size="lg">
          {t`System Administrator`}
        </Title>
        <EmptyStateBody>
          {t`System administrators have unrestricted access to all resources.`}
        </EmptyStateBody>
      </EmptyState>
    );
  }

  return (
    <>
      <PaginatedTable
        contentError={contentError}
        hasContentLoading={isLoading || isDisassociateLoading}
        items={roles}
        itemCount={roleCount}
        pluralizedItemName={t`Team Roles`}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={[
          {
            name: t`Role`,
            key: 'role_field__icontains',
            isDefault: true,
          },
        ]}
        toolbarSortColumns={[
          {
            name: t`ID`,
            key: 'id',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [
                    <ToolbarAddButton
                      ouiaId="role-add-button"
                      key="add"
                      onClick={() => setShowAddModal(true)}
                    />,
                  ]
                : []),
            ]}
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG} isSelectable={false}>
            <HeaderCell>{t`Resource Name`}</HeaderCell>
            <HeaderCell>{t`Type`}</HeaderCell>
            <HeaderCell sortKey="id">{t`Role`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(role, index) => (
          <TeamRoleListItem
            key={role.id}
            role={role}
            detailUrl={detailUrl(role)}
            onDisassociate={setRoleToDisassociate}
            index={index}
          />
        )}
      />
      {showAddModal && (
        <UserAndTeamAccessAdd
          apiModel={TeamsAPI}
          onFetchData={() => {
            setShowAddModal(false);
            fetchRoles();
          }}
          title={t`Add team permissions`}
          onClose={() => setShowAddModal(false)}
          onError={(err) => setAssociateError(err)}
        />
      )}
      {roleToDisassociate && (
        <AlertModal
          aria-label={t`Disassociate role`}
          isOpen={roleToDisassociate}
          variant="error"
          title={t`Disassociate role!`}
          onClose={() => setRoleToDisassociate(null)}
          actions={[
            <Button
              ouiaId="disassociate-confirm-button"
              key="disassociate"
              variant="danger"
              aria-label={t`confirm disassociate`}
              onClick={disassociateRole}
            >
              {t`Disassociate`}
            </Button>,
            <Button
              ouiaId="disassociate-cancel-button"
              key="cancel"
              variant="link"
              aria-label={t`Cancel`}
              onClick={() => setRoleToDisassociate(null)}
            >
              {t`Cancel`}
            </Button>,
          ]}
        >
          <div>
            {t`This action will disassociate the following role from ${roleToDisassociate.summary_fields.resource_name}:`}
            <br />
            <strong>{roleToDisassociate.name}</strong>
          </div>
        </AlertModal>
      )}
      {associateError && (
        <AlertModal
          aria-label={t`Associate role error`}
          isOpen={associateError}
          variant="error"
          title={t`Error!`}
          onClose={() => setAssociateError(null)}
        >
          {t`Failed to associate role`}
          <ErrorDetail error={associateError} />
        </AlertModal>
      )}
      {disassociationError && (
        <AlertModal
          isOpen={disassociationError}
          variant="error"
          title={t`Error!`}
          onClose={clearDisassociationError}
        >
          {t`Failed to delete role.`}
          <ErrorDetail error={disassociationError} />
        </AlertModal>
      )}
    </>
  );
}
export default TeamRolesList;
