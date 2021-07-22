import React from 'react';

import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';

function RevertAllAlert({ onClose, onRevertAll }) {
  return (
    <AlertModal
      isOpen
      title={t`Revert settings`}
      variant="info"
      onClose={onClose}
      ouiaId="revert-all-modal"
      actions={[
        <Button
          ouiaId="revert-all-confirm-button"
          key="revert"
          variant="primary"
          aria-label={t`Confirm revert all`}
          onClick={onRevertAll}
        >
          {t`Revert all`}
        </Button>,
        <Button
          ouiaId="revert-all-cancel-button"
          key="cancel"
          variant="link"
          aria-label={t`Cancel revert`}
          onClick={onClose}
        >
          {t`Cancel`}
        </Button>,
      ]}
    >
      {t`This will revert all configuration values on this page to
      their factory defaults. Are you sure you want to proceed?`}
    </AlertModal>
  );
}

export default RevertAllAlert;
