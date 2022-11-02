/* eslint-disable react/jsx-no-useless-fragment */
import React from 'react';
import { func, string } from 'prop-types';
import { Button } from '@patternfly/react-core';

import { t } from '@lingui/macro';

import { Role } from 'types';
import AlertModal from '../AlertModal';

function DeleteRoleConfirmationModal({ role, username, onCancel, onConfirm }) {
  const sourceOfRole = () =>
    typeof role.team_id !== 'undefined' ? t`Team` : t`User`;
  const title = t`Remove ${sourceOfRole()} Access`;
  return (
    <AlertModal
      variant="danger"
      title={title}
      isOpen
      onClose={onCancel}
      actions={[
        <Button
          ouiaId="delete-role-modal-delete-button"
          key="delete"
          variant="danger"
          aria-label={t`Confirm delete`}
          onClick={onConfirm}
        >
          {t`Delete`}
        </Button>,
        <Button
          ouiaId="delete-role-modal-cancel-button"
          key="cancel"
          variant="link"
          onClick={onCancel}
        >
          {t`Cancel`}
        </Button>,
      ]}
    >
      {sourceOfRole() === 'Team' ? (
        <>
          {t`Are you sure you want to remove ${role.name} access from ${role.team_name}?  Doing so affects all members of the team.`}
          <br />
          <br />
          {t`If you only want to remove access for this particular user, please remove them from the team.`}
        </>
      ) : (
        <>
          {t`Are you sure you want to remove ${role.name} access from ${username}?`}
        </>
      )}
    </AlertModal>
  );
}

DeleteRoleConfirmationModal.propTypes = {
  role: Role.isRequired,
  username: string,
  onCancel: func.isRequired,
  onConfirm: func.isRequired,
};

DeleteRoleConfirmationModal.defaultProps = {
  username: '',
};

export default DeleteRoleConfirmationModal;
