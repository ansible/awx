import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useLocation } from 'react-router-dom';
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
import { getQSConfig, parseQueryString } from '../../../util/qs';
import { UsersAPI, RolesAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import PaginatedDataList from '../../../components/PaginatedDataList';
import ErrorDetail from '../../../components/ErrorDetail';
import AlertModal from '../../../components/AlertModal';

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

  const [roleToDisassociate, setRoleToDisassociate] = useState(null);
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

  const {
    isLoading: isDisassociateLoading,
    deleteItems: disassociateRole,
    deletionError: disassociationError,
    clearDeletionError: clearDisassociationError,
  } = useDeleteItems(
    useCallback(async () => {
      setRoleToDisassociate(null);
      await RolesAPI.disassociateUserRole(
        roleToDisassociate.id,
        parseInt(id, 10)
      );
    }, [roleToDisassociate, id]),
    { qsConfig: QS_CONFIG, fetchItems: fetchRoles }
  );

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
        contentError={error}
        hasContentLoading={isLoading || isDisassociateLoading}
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
              isSelected={false}
              onSelect={item => {
                setRoleToDisassociate(item);
              }}
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
export default withI18n()(UserAccessList);
