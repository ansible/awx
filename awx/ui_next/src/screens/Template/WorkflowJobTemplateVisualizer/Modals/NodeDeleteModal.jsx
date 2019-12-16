import React, { Fragment } from 'react';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import AlertModal from '@components/AlertModal';

function NodeDeleteModal({ i18n, nodeToDelete, onConfirm, onCancel }) {
  return (
    <AlertModal
      variant="danger"
      title="Remove Node"
      isOpen={nodeToDelete}
      onClose={onCancel}
      actions={[
        <Button
          key="remove"
          variant="danger"
          aria-label={i18n._(t`Confirm node removal`)}
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
      {nodeToDelete && nodeToDelete.unifiedJobTemplate ? (
        <Fragment>
          <p>{i18n._(t`Are you sure you want to remove the node below:`)}</p>
          <br />
          <strong css="color: var(--pf-global--danger-color--100)">
            {nodeToDelete.unifiedJobTemplate.name}
          </strong>
        </Fragment>
      ) : (
        <p>{i18n._(t`Are you sure you want to remove this node?`)}</p>
      )}
    </AlertModal>
  );
}

export default withI18n()(NodeDeleteModal);
