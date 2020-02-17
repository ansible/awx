import React, { useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import AlertModal from '@components/AlertModal';
import { Button } from '@patternfly/react-core';
import { CardBody, CardActionsRow } from '@components/Card';
import ContentLoading from '@components/ContentLoading';
import DeleteButton from '@components/DeleteButton';
import { DetailList, Detail } from '@components/DetailList';
import ErrorDetail from '@components/ErrorDetail';
import { formatDateString } from '@util/dates';
import { UsersAPI } from '@api';

function UserDetail({ user, i18n }) {
  const {
    id,
    username,
    email,
    first_name,
    last_name,
    last_login,
    created,
    is_superuser,
    is_system_auditor,
    summary_fields,
  } = user;
  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(false);
  const history = useHistory();

  const handleDelete = async () => {
    setHasContentLoading(true);
    try {
      await UsersAPI.destroy(id);
      history.push(`/users`);
    } catch (error) {
      setDeletionError(error);
    }
    setHasContentLoading(false);
  };

  let user_type;
  if (is_superuser) {
    user_type = i18n._(t`System Administrator`);
  } else if (is_system_auditor) {
    user_type = i18n._(t`System Auditor`);
  } else {
    user_type = i18n._(t`Normal User`);
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  return (
    <CardBody>
      <DetailList>
        <Detail
          label={i18n._(t`Username`)}
          value={username}
          dataCy="user-detail-username"
        />
        <Detail label={i18n._(t`Email`)} value={email} />
        <Detail label={i18n._(t`First Name`)} value={`${first_name}`} />
        <Detail label={i18n._(t`Last Name`)} value={`${last_name}`} />
        <Detail label={i18n._(t`User Type`)} value={`${user_type}`} />
        {last_login && (
          <Detail
            label={i18n._(t`Last Login`)}
            value={formatDateString(last_login)}
          />
        )}
        <Detail label={i18n._(t`Created`)} value={formatDateString(created)} />
      </DetailList>
      <CardActionsRow>
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.edit && (
            <Button
              aria-label={i18n._(t`edit`)}
              component={Link}
              to={`/users/${id}/edit`}
            >
              {i18n._(t`Edit`)}
            </Button>
          )}
        {summary_fields.user_capabilities &&
          summary_fields.user_capabilities.delete && (
            <DeleteButton
              name={username}
              modalTitle={i18n._(t`Delete User`)}
              onConfirm={handleDelete}
            >
              {i18n._(t`Delete`)}
            </DeleteButton>
          )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete user.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default withI18n()(UserDetail);
