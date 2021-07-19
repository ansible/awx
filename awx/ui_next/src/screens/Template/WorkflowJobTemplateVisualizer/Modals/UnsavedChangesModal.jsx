import React, { useContext } from 'react';
import { Button, Modal } from '@patternfly/react-core';

import { t, Trans } from '@lingui/macro';
import { func } from 'prop-types';
import { WorkflowDispatchContext } from 'contexts/Workflow';

function UnsavedChangesModal({ onSaveAndExit, onExit }) {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <Modal
      width={600}
      isOpen
      title={t`Warning: Unsaved Changes`}
      aria-label={t`Unsaved changes modal`}
      onClose={() => dispatch({ type: 'TOGGLE_UNSAVED_CHANGES_MODAL' })}
      actions={[
        <Button
          ouiaId="unsaved-changes-exit-button"
          id="confirm-exit-without-saving"
          key="exit"
          variant="danger"
          aria-label={t`Exit Without Saving`}
          onClick={onExit}
        >
          {t`Exit Without Saving`}
        </Button>,
        <Button
          ouiaId="unsaved-changes-save-exit-button"
          id="confirm-save-and-exit"
          key="save"
          variant="primary"
          aria-label={t`Save & Exit`}
          onClick={onSaveAndExit}
        >
          {t`Save & Exit`}
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
  onExit: func.isRequired,
  onSaveAndExit: func.isRequired,
};

export default UnsavedChangesModal;
