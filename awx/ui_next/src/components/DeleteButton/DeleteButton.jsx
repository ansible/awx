import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';

function DeleteButton({
  onConfirm,
  modalTitle,
  name,
  i18n,
  variant,
  children,
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button
        variant={variant || 'danger'}
        aria-label={i18n._(t`Delete`)}
        onClick={() => setIsOpen(true)}
      >
        {children || i18n._(t`Delete`)}
      </Button>
      <AlertModal
        isOpen={isOpen}
        title={modalTitle}
        variant="danger"
        onClose={() => setIsOpen(false)}
        actions={[
          <Button
            key="delete"
            variant="danger"
            aria-label={i18n._(t`Delete`)}
            onClick={onConfirm}
          >
            {i18n._(t`Delete`)}
          </Button>,
          <Button
            key="cancel"
            variant="secondary"
            aria-label={i18n._(t`Cancel`)}
            onClick={() => setIsOpen(false)}
          >
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        {i18n._(t`Are you sure you want to delete:`)}
        <br />
        <strong>{name}</strong>
      </AlertModal>
    </>
  );
}

export default withI18n()(DeleteButton);
