import React, { useContext } from 'react';
import { Button, Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { func } from 'prop-types';
import { WorkflowDispatchContext } from '../../../../contexts/Workflow';

function UnsavedChangesModal({ i18n, onSaveAndExit, onExit }) {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <Modal
      width={600}
      isOpen
      title={i18n._(t`Warning: Unsaved Changes`)}
      aria-label={i18n._(t`Unsaved changes modal`)}
      onClose={() => dispatch({ type: 'TOGGLE_UNSAVED_CHANGES_MODAL' })}
      actions={[
        <Button
          id="confirm-exit-without-saving"
          key="exit"
          variant="danger"
          aria-label={i18n._(t`Exit Without Saving`)}
          onClick={onExit}
        >
          {i18n._(t`Exit Without Saving`)}
        </Button>,
        <Button
          id="confirm-save-and-exit"
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
  onExit: func.isRequired,
  onSaveAndExit: func.isRequired,
};

export default withI18n()(UnsavedChangesModal);
