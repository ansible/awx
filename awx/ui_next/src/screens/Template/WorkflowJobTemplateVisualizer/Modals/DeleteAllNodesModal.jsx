import React from 'react';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func } from 'prop-types';
import AlertModal from '@components/AlertModal';

function DeleteAllNodesModal({ i18n, onConfirm, onCancel }) {
  return (
    <AlertModal
      actions={[
        <Button
          key="remove"
          variant="danger"
          aria-label={i18n._(t`Confirm removal of all nodes`)}
          onClick={() => onConfirm()}
        >
          {i18n._(t`Remove`)}
        </Button>,
        <Button
          key="cancel"
          variant="secondary"
          aria-label={i18n._(t`Cancel node removal`)}
          onClick={onCancel}
        >
          {i18n._(t`Cancel`)}
        </Button>,
      ]}
      isOpen
      onClose={onCancel}
      title={i18n._(t`Remove All Nodes`)}
      variant="danger"
    >
      <p>
        {i18n._(
          t`Are you sure you want to remove all the nodes in this workflow?`
        )}
      </p>
    </AlertModal>
  );
}

DeleteAllNodesModal.propTypes = {
  onCancel: func.isRequired,
  onConfirm: func.isRequired,
};

export default withI18n()(DeleteAllNodesModal);
