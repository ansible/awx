import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import AlertModal from '../AlertModal';

function DeleteButton({
  onConfirm,
  modalTitle,
  name,
  i18n,
  variant,
  children,
  isDisabled,
  ouiaId,
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button
        variant={variant || 'secondary'}
        aria-label={i18n._(t`Delete`)}
        isDisabled={isDisabled}
        onClick={() => setIsOpen(true)}
        ouiaId={ouiaId}
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
            ouiaId="delete-modal-confirm"
            key="delete"
            variant="danger"
            aria-label={i18n._(t`Delete`)}
            isDisabled={isDisabled}
            onClick={onConfirm}
          >
            {i18n._(t`Delete`)}
          </Button>,
          <Button
            ouiaId="delete-modal-cancel"
            key="cancel"
            variant="link"
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

DeleteButton.propTypes = {
  ouiaId: PropTypes.string,
};

DeleteButton.defaultProps = {
  ouiaId: null,
};

export default withI18n()(DeleteButton);
