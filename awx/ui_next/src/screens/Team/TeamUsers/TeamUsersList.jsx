import React, { useEffect, useCallback, useState } from 'react';
import { useLocation, useRouteMatch, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Button } from '@patternfly/react-core';
import { TeamsAPI, UsersAPI } from '../../../api';
import useRequest, { useDeleteItems } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal';
import DataListToolbar from '../../../components/DataListToolbar';
import ErrorDetail from '../../../components/ErrorDetail';
import PaginatedDataList, {
  ToolbarAddButton,
} from '../../../components/PaginatedDataList';
import { getQSConfig, parseQueryString } from '../../../util/qs';

import TeamUserListItem from './TeamUserListItem';

const QS_CONFIG = getQSConfig('user', {
  page: 1,
  page_size: 20,
  order_by: 'username',
});

function TeamUsersList({ i18n }) {
  const location = useLocation();
  const match = useRouteMatch();
  const { id: teamId } = useParams();
  const [roleToDisassociate, setRoleToDisassociate] = useState([]);

  const {
    result: { users, itemCount, actions },
    error: contentError,
    isLoading,
    request: fetchRoles,
  } = useRequest(
    useCallback(async () => {
      const params = parseQueryString(QS_CONFIG, location.search);
      const [response, actionsResponse] = await Promise.all([
        TeamsAPI.readUsersAccess(teamId, params),
        TeamsAPI.readUsersAccessOptions(teamId),
      ]);
      return {
        users: response.data.results,
        itemCount: response.data.count,
        actions: actionsResponse.data.actions,
      };
    }, [location, teamId]),
    {
      users: [],
      itemCount: 0,
      actions: {},
    }
  );

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const {
    isLoading: isDeleteLoading,
    deleteItems: disassociateRole,
    deletionError,
    clearDeletionError,
  } = useDeleteItems(
    useCallback(async () => {
      UsersAPI.disassociateRole(
        roleToDisassociate[0].id,
        roleToDisassociate[1].id
      );
    }, [roleToDisassociate]),
    {
      qsConfig: QS_CONFIG,
      fetchItems: fetchRoles,
    }
  );

  const handleRoleDisassociation = async () => {
    await disassociateRole();
    setRoleToDisassociate(null);
  };

  const hasContentLoading = isDeleteLoading || isLoading;
  const canAdd = actions && actions.POST;
  return (
    <>
      <PaginatedDataList
        contentError={contentError}
        hasContentLoading={hasContentLoading}
        items={users}
        itemCount={itemCount}
        pluralizedItemName={i18n._(t`Users`)}
        qsConfig={QS_CONFIG}
        toolbarSearchColumns={[
          {
            name: i18n._(t`User Name`),
            key: 'username',
            isDefault: true,
          },
          {
            name: i18n._(t`First Name`),
            key: 'first_name',
          },
          {
            name: i18n._(t`Last Name`),
            key: 'last_name',
          },
          {
            name: i18n._(t`Email`),
            key: 'email',
          },
        ]}
        toolbarSortColumns={[
          {
            name: i18n._(t`User Name`),
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
          {
            name: i18n._(t`Email`),
            key: 'email',
          },
        ]}
        renderToolbar={props => (
          <DataListToolbar
            {...props}
            qsConfig={QS_CONFIG}
            additionalControls={[
              ...(canAdd
                ? [<ToolbarAddButton key="add" linkTo="/users/add" />]
                : []),
            ]}
          />
        )}
        renderItem={user => (
          <TeamUserListItem
            key={user.id}
            user={user}
            detailUrl={`/users/${user.id}/details`}
            disassociateRole={role => setRoleToDisassociate([user, role])}
          />
        )}
        emptyStateControls={
          canAdd ? (
            <ToolbarAddButton key="add" linkTo={`${match.url}/add`} />
          ) : null
        }
      />
      {roleToDisassociate?.length > 0 && (
        <AlertModal
          variant="danger"
          title={i18n._(t`Disassociate roles`)}
          isOpen={roleToDisassociate}
          onClose={() => setRoleToDisassociate(null)}
          actions={[
            <Button
              key="disassociate"
              variant="danger"
              aria-label={i18n._(t`confirm disassociation`)}
              onClick={() => handleRoleDisassociation()}
            >
              {i18n._(t`Disassociate`)}
            </Button>,
            <Button
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`cancel disassociation`)}
              onClick={() => setRoleToDisassociate(null)}
            >
              {i18n._(t`Cancel`)}
            </Button>,
          ]}
        >
          <div>{i18n._(t`This action will disassociate the following:`)}</div>
          <span>{roleToDisassociate.name}</span>
        </AlertModal>
      )}
      <AlertModal
        isOpen={deletionError}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={clearDeletionError}
      >
        {i18n._(t`Failed to disassociate one or more roles.`)}
        <ErrorDetail error={deletionError} />
      </AlertModal>
    </>
  );
}

export default withI18n()(TeamUsersList);
