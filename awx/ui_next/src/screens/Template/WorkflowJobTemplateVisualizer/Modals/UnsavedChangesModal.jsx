import React from 'react';
import { Button, Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { func } from 'prop-types';

function UnsavedChangesModal({ i18n, onCancel, onSaveAndExit, onExit }) {
  return (
    <Modal
      width={600}
      isOpen
      title={i18n._(t`Warning: Unsaved Changes`)}
      onClose={onCancel}
      actions={[
        <Button
          key="exit"
          variant="danger"
          aria-label={i18n._(t`Exit Without Saving`)}
          onClick={onExit}
        >
          {i18n._(t`Exit Without Saving`)}
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

UnsavedChangesModal.propTypes = {
  onCancel: func.isRequired,
  onExit: func.isRequired,
  onSaveAndExit: func.isRequired,
};

export default withI18n()(UnsavedChangesModal);
