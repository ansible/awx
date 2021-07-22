import React, { useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';

import { Button, Label } from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import DeleteButton from 'components/DeleteButton';
import { DetailList, Detail } from 'components/DetailList';
import ErrorDetail from 'components/ErrorDetail';
import { formatDateString } from 'util/dates';
import { UsersAPI } from 'api';
import useRequest, { useDismissableError } from 'hooks/useRequest';

function UserDetail({ user }) {
  const {
    id,
    username,
    email,
    first_name,
    last_name,
    last_login,
    created,
    modified,
    is_superuser,
    is_system_auditor,
    summary_fields,
  } = user;
  const history = useHistory();

  const {
    request: deleteUser,
    isLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await UsersAPI.destroy(id);
      history.push(`/users`);
    }, [id, history])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  let user_type;
  if (is_superuser) {
    user_type = t`System Administrator`;
  } else if (is_system_auditor) {
    user_type = t`System Auditor`;
  } else {
    user_type = t`Normal User`;
  }

  let userAuthType;
  if (user.ldap_dn) {
    userAuthType = t`LDAP`;
  } else if (user.auth.length > 0) {
    userAuthType = t`SOCIAL`;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail label={t`First Name`} value={`${first_name}`} />
        <Detail label={t`Last Name`} value={`${last_name}`} />
        <Detail label={t`Email`} value={email} />
        <Detail
          label={t`Username`}
          value={username}
          dataCy="user-detail-username"
        />
        <Detail label={t`User Type`} value={`${user_type}`} />
        {userAuthType && (
          <Detail
            label={t`Type`}
            value={<Label aria-label={t`login type`}>{userAuthType}</Label>}
          />
        )}
        {last_login && (
          <Detail label={t`Last Login`} value={formatDateString(last_login)} />
        )}
        <Detail label={t`Created`} value={formatDateString(created)} />
        {modified && (
          <Detail label={t`Last Modified`} value={formatDateString(modified)} />
        )}
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              ouiaId="user-detail-edit-button"
              aria-label={t`edit`}
              component={Link}
              to={`/users/${id}/edit`}
            >
              {t`Edit`}
            </Button>
          )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={username}
              modalTitle={t`Delete User`}
              onConfirm={deleteUser}
              isDisabled={isLoading}
            >
              {t`Delete`}
            </DeleteButton>
          )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete user.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default UserDetail;
