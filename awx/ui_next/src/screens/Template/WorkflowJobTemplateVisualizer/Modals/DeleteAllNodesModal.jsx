import React from 'react';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '@components/AlertModal';

function DeleteAllNodesModal({ i18n, onConfirm, onCancel }) {
  return (
    <AlertModal
      variant="danger"
      title={i18n._(t`Remove All Nodes`)}
      isOpen={true}
      onClose={onCancel}
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
    >
      <p>
        {i18n._(
          t`Are you sure you want to remove all the nodes in this workflow?`
        )}
      </p>
    </AlertModal>
  );
}

export default withI18n()(DeleteAllNodesModal);
