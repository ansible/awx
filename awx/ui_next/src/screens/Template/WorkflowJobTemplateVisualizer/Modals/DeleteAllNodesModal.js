import React, { useContext } from 'react';
import { Button } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from 'contexts/Workflow';
import AlertModal from 'components/AlertModal';

function DeleteAllNodesModal() {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <AlertModal
      actions={[
        <Button
          ouiaId="delete-all-confirm-button"
          id="confirm-delete-all-nodes"
          key="remove"
          variant="danger"
          aria-label={t`Confirm removal of all nodes`}
          onClick={() => dispatch({ type: 'DELETE_ALL_NODES' })}
        >
          {t`Remove`}
        </Button>,
        <Button
          ouiaId="delete-all-cancel-button"
          id="cancel-delete-all-nodes"
          key="cancel"
          variant="link"
          aria-label={t`Cancel node removal`}
          onClick={() => dispatch({ type: 'TOGGLE_DELETE_ALL_NODES_MODAL' })}
        >
          {t`Cancel`}
        </Button>,
      ]}
      isOpen
      onClose={() => dispatch({ type: 'TOGGLE_DELETE_ALL_NODES_MODAL' })}
      title={t`Remove All Nodes`}
      variant="danger"
    >
      <p>
        {t`Are you sure you want to remove all the nodes in this workflow?`}
      </p>
    </AlertModal>
  );
}

export default DeleteAllNodesModal;
