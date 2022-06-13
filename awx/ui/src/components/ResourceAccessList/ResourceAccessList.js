import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { t } from '@lingui/macro';
import { RolesAPI, TeamsAPI, UsersAPI, OrganizationsAPI } from 'api';
import { getQSConfig, parseQueryString } from 'util/qs';
import useRequest, { useDeleteItems } from 'hooks/useRequest';
import { useUserProfile, useConfig } from 'contexts/Config';
import AddResourceRole from '../AddRole/AddResourceRole';
import AlertModal from '../AlertModal';
import DataListToolbar from '../DataListToolbar';
import PaginatedTable, {
  HeaderRow,
  HeaderCell,
  ToolbarAddButton,
  getSearchableKeys,
} from '../PaginatedTable';
import DeleteRoleConfirmationModal from './DeleteRoleConfirmationModal';
import ResourceAccessListItem from './ResourceAccessListItem';
import ErrorDetail from '../ErrorDetail';

const QS_CONFIG = getQSConfig('access', {
  page: 1,
  page_size: 5,
  order_by: 'first_name',
});

function ResourceAccessList({ apiModel, resource }) {
  const { isSuperUser, isOrgAdmin } = useUserProfile();
  const { me } = useConfig();
  const [submitError, setSubmitError] = useState(null);
  const [deletionRecord, setDeletionRecord] = useState(null);
  const [deletionRole, setDeletionRole] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const location = useLocation();

  const {
    isLoading: isFetchingOrgAdmins,
    error: errorFetchingOrgAdmins,
    request: fetchOrgAdmins,
    result: { isCredentialOrgAdmin },
  } = useRequest(
    useCallback(async () => {
      if (
        isSuperUser ||
        resource.type !== 'credential' ||
        !isOrgAdmin ||
        !resource?.organization
      ) {
        return false;
      }
      const {
        data: { count },
      } = await OrganizationsAPI.readAdmins(resource.organization, {
        id: me.id,
      });
      return { isCredentialOrgAdmin: !!count };
    }, [me.id, isOrgAdmin, isSuperUser, resource.type, resource.organization]),
    {
      isCredentialOrgAdmin: false,
    }
  );

  useEffect(() => {
    fetchOrgAdmins();
  }, [fetchOrgAdmins]);

  let canAddAdditionalControls = false;
  if (isSuperUser) {
    canAddAdditionalControls = true;
  }
  if (resource.type === 'credential' && isOrgAdmin && isCredentialOrgAdmin) {
    canAddAdditionalControls = true;
  }
  if (resource.type !== 'credential') {
    canAddAdditionalControls =
      resource?.summary_fields?.user_capabilities?.edit;
  }

  const {
    result: {
      accessRecords,
      itemCount,
      relatedSearchableKeys,
      searchableKeys,
      organizationRoles,
    },
    error: contentError,
    isLoading,
    request: fetchAccessRecords,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        apiModel.readAccessList(resource.id, params),
        apiModel.readAccessOptions(resource.id),
      ]);

      // Eventually this could be expanded to other access lists.
      // We will need to combine the role ids of all the different level
      // of resource level roles.

      let orgRoles;
      if (location.pathname.includes('/organizations')) {
        const [
          {
            data: { results: systemAdmin },
          },
          {
            data: { results: systemAuditor },
          },
        ] = await Promise.all([
          RolesAPI.read({ singleton_name: 'system_administrator' }),
          RolesAPI.read({ singleton_name: 'system_auditor' }),
        ]);

        orgRoles = Object.entries(resource.summary_fields.object_roles).map(
          ([key, value]) => {
            if (key === 'admin_role') {
              return [`${value.id}, ${systemAdmin[0].id}`, value.name];
            }

            if (key === 'auditor_role') {
              return [`${value.id}, ${systemAuditor[0].id}`, value.name];
            }

            return [`${value.id}`, value.name];
          }
        );
      }
      return {
        accessRecords: response.data.results,
        itemCount: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map((val) => val.slice(0, -8)),
        searchableKeys: getSearchableKeys(actionsResponse.data.actions?.GET),
        organizationRoles: orgRoles,
      };
    }, [apiModel, location, resource]),
    {
      accessRecords: [],
      itemCount: 0,
      relatedSearchableKeys: [],
      searchableKeys: [],
    }
  );

  useEffect(() => {
    fetchAccessRecords();
  }, [fetchAccessRecords]);

  const {
    isLoading: isDeleteLoading,
    deleteItems: deleteRole,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(() => {
      if (typeof deletionRole.team_id !== 'undefined') {
        return TeamsAPI.disassociateRole(deletionRole.team_id, deletionRole.id);
      }
      return UsersAPI.disassociateRole(deletionRecord.id, deletionRole.id);
      /* eslint-disable-next-line react-hooks/exhaustive-deps */
    }, [deletionRole]),
    {
      qsConfig: QS_CONFIG,
      fetchItems: fetchAccessRecords,
    }
  );
  const toolbarSearchColumns = [
    {
      name: t`Username`,
      key: 'username__icontains',
      isDefault: true,
    },
    {
      name: t`First Name`,
      key: 'first_name__icontains',
    },
    {
      name: t`Last Name`,
      key: 'last_name__icontains',
    },
  ];

  if (organizationRoles?.length > 0) {
    toolbarSearchColumns.push({
      name: t`Roles`,
      key: `or__roles__in`,
      options: organizationRoles,
    });
  }

  return (
    <>
      <PaginatedTable
        error={contentError || errorFetchingOrgAdmins}
        hasContentLoading={isLoading || isDeleteLoading || isFetchingOrgAdmins}
        items={accessRecords}
        itemCount={itemCount}
        pluralizedItemName={t`Roles`}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={toolbarSearchColumns}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={(props) => (
          <DataListToolbar
            {...props}
            qsConfig={QS_CONFIG}
            additionalControls={
              canAddAdditionalControls
                ? [
                    <ToolbarAddButton
                      ouiaId="access-add-button"
                      key="add"
                      onClick={() => setShowAddModal(true)}
                    />,
                  ]
                : []
            }
          />
        )}
        headerRow={
          <HeaderRow qsConfig={QS_CONFIG} isSelectable={false}>
            <HeaderCell sortKey="username">{t`Username`}</HeaderCell>
            <HeaderCell sortKey="first_name">{t`First name`}</HeaderCell>
            <HeaderCell sortKey="last_name">{t`Last name`}</HeaderCell>
            <HeaderCell>{t`Roles`}</HeaderCell>
          </HeaderRow>
        }
        renderRow={(accessRecord, index) => (
          <ResourceAccessListItem
            key={accessRecord.id}
            accessRecord={accessRecord}
            onRoleDelete={(role, record) => {
              setDeletionRecord(record);
              setDeletionRole(role);
              setShowDeleteModal(true);
            }}
            rowIndex={index}
          />
        )}
      />
      {showAddModal && (
        <AddResourceRole
          onClose={() => setShowAddModal(false)}
          onSave={() => {
            setShowAddModal(false);
            fetchAccessRecords();
          }}
          onError={(err) => setSubmitError(err)}
          roles={resource.summary_fields.object_roles}
          resource={resource}
        />
      )}
      {showDeleteModal && (
        <DeleteRoleConfirmationModal
          role={deletionRole}
          username={deletionRecord.username}
          onCancel={() => {
            setDeletionRecord(null);
            setDeletionRole(null);
            setShowDeleteModal(false);
          }}
          onConfirm={async () => {
            await deleteRole();
            setShowDeleteModal(false);
            setDeletionRecord(null);
            setDeletionRole(null);
          }}
        />
      )}
      {submitError && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen={submitError}
          onClose={() => setSubmitError(null)}
        >
          {t`Failed to assign roles properly`}
          <ErrorDetail error={submitError} />
        </AlertModal>
      )}
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={t`Error!`}
          onClose={clearDeletionError}
        >
          {t`Failed to delete role`}
        </AlertModal>
      )}
    </>
  );
}
export default ResourceAccessList;
