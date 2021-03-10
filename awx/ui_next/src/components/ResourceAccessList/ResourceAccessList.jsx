import React, { useCallback, useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { RolesAPI, TeamsAPI, UsersAPI } from '../../api';
import AddResourceRole from '../AddRole/AddResourceRole';
import AlertModal from '../AlertModal';
import DataListToolbar from '../DataListToolbar';
import PaginatedDataList, { ToolbarAddButton } from '../PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../util/qs';
import useRequest, { useDeleteItems } from '../../util/useRequest';
import DeleteRoleConfirmationModal from './DeleteRoleConfirmationModal';
import ResourceAccessListItem from './ResourceAccessListItem';

const QS_CONFIG = getQSConfig('access', {
  page: 1,
  page_size: 5,
  order_by: 'first_name',
});

function ResourceAccessList({ i18n, apiModel, resource }) {
  const [deletionRecord, setDeletionRecord] = useState(null);
  const [deletionRole, setDeletionRole] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const location = useLocation();

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
        const {
          data: { results: roles },
        } = await RolesAPI.read({ content_type__isnull: true });
        const sysAdmin = roles.filter(
          role => role.name === 'System Administrator'
        );
        const sysAud = roles.filter(role => {
          let auditor;
          if (role.name === 'System Auditor') {
            auditor = role.id;
          }
          return auditor;
        });

        orgRoles = Object.values(resource.summary_fields.object_roles).map(
          opt => {
            let item;
            if (opt.name === 'Admin') {
              item = [`${opt.id}, ${sysAdmin[0].id}`, opt.name];
            } else if (sysAud[0].id && opt.name === 'Auditor') {
              item = [`${sysAud[0].id}, ${opt.id}`, opt.name];
            } else {
              item = [`${opt.id}`, opt.name];
            }
            return item;
          }
        );
      }
      return {
        accessRecords: response.data.results,
        itemCount: response.data.count,
        relatedSearchableKeys: (
          actionsResponse?.data?.related_search_fields || []
        ).map(val => val.slice(0, -8)),
        searchableKeys: Object.keys(
          actionsResponse.data.actions?.GET || {}
        ).filter(key => actionsResponse.data.actions?.GET[key].filterable),
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
      name: i18n._(t`Username`),
      key: 'username__icontains',
      isDefault: true,
    },
    {
      name: i18n._(t`First Name`),
      key: 'first_name__icontains',
    },
    {
      name: i18n._(t`Last Name`),
      key: 'last_name__icontains',
    },
  ];

  if (organizationRoles?.length > 0) {
    toolbarSearchColumns.push({
      name: i18n._(t`Roles`),
      key: `or__roles__in`,
      options: organizationRoles,
    });
  }

  return (
    <>
      <PaginatedDataList
        error={contentError}
        hasContentLoading={isLoading || isDeleteLoading}
        items={accessRecords}
        itemCount={itemCount}
        pluralizedItemName={i18n._(t`Roles`)}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={toolbarSearchColumns}
        toolbarSortColumns={[
          {
            name: i18n._(t`Username`),
            key: 'username',
          },
          {
            name: i18n._(t`First Name`),
            key: 'first_name',
          },
          {
            name: i18n._(t`Last Name`),
            key: 'last_name',
          },
        ]}
        toolbarSearchableKeys={searchableKeys}
        toolbarRelatedSearchableKeys={relatedSearchableKeys}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            qsConfig={QS_CONFIG}
            additionalControls={
              resource?.summary_fields?.user_capabilities?.edit
                ? [
                    <ToolbarAddButton
                      key="add"
                      onClick={() => setShowAddModal(true)}
                    />,
                  ]
                : []
            }
          />
        )}
        renderItem={accessRecord => (
          <ResourceAccessListItem
            key={accessRecord.id}
            accessRecord={accessRecord}
            onRoleDelete={(role, record) => {
              setDeletionRecord(record);
              setDeletionRole(role);
              setShowDeleteModal(true);
            }}
            i18n={i18n}
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
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={clearDeletionError}
        >
          {i18n._(t`Failed to delete role`)}
        </AlertModal>
      )}
    </>
  );
}
export default withI18n()(ResourceAccessList);
