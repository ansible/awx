import React from 'react';
import { Button, Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';
import { t } from '@lingui/macro';

function UnsavedChangesModal({ i18n, onCancel, onSaveAndExit, onExit }) {
  return (
    <Modal
      width={600}
      isOpen={true}
      title={i18n._(t`Warning: Unsaved Changes`)}
      onClose={onCancel}
      actions={[
        <Button
          key="exit"
          variant="danger"
          aria-label={i18n._(t`Exit`)}
          onClick={onExit}
        >
          {i18n._(t`Exit`)}
        </Button>,
        <Button
          key="save"
          variant="primary"
          aria-label={i18n._(t`Save & Exit`)}
          onClick={onSaveAndExit}
        >
          {i18n._(t`Save & Exit`)}
        </Button>,
      ]}
    >
      <p>
        <Trans>
          Are you sure you want to exit the Workflow Creator without saving your
          changes?
        </Trans>
      </p>
    </Modal>
  );
}

export default withI18n()(UnsavedChangesModal);
