import 'styled-components/macro';
import React, { useContext } from 'react';
import { Button } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import AlertModal from 'components/AlertModal';
import { stringIsUUID } from 'util/strings';

function NodeDeleteModal() {
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToDelete } = useContext(WorkflowStateContext);
  const identifier = nodeToDelete?.originalNodeObject?.identifier;
  const nodeIdentifier =
    identifier && !stringIsUUID(identifier)
      ? identifier
      : nodeToDelete?.identifier;
  const unifiedJobTemplate =
    nodeToDelete?.fullUnifiedJobTemplate ||
    nodeToDelete?.originalNodeObject?.summary_fields?.unified_job_template;
  const nodeName = nodeIdentifier || unifiedJobTemplate?.name;
  return (
    <AlertModal
      variant="danger"
      title={t`Remove Node ${nodeName}`}
      isOpen={nodeToDelete}
      onClose={() => dispatch({ type: 'SET_NODE_TO_DELETE', value: null })}
      actions={[
        <Button
          ouiaId="node-removal-confirm-button"
          id="confirm-node-removal"
          key="remove"
          variant="danger"
          aria-label={t`Confirm node removal`}
          onClick={() => dispatch({ type: 'DELETE_NODE' })}
        >
          {t`Remove`}
        </Button>,
        <Button
          ouiaId="node-removal-cancel-button"
          id="cancel-node-removal"
          key="cancel"
          variant="link"
          aria-label={t`Cancel node removal`}
          onClick={() => dispatch({ type: 'SET_NODE_TO_DELETE', value: null })}
        >
          {t`Cancel`}
        </Button>,
      ]}
    >
      {nodeToDelete && nodeToDelete.unifiedJobTemplate ? (
        <>
          <p>{t`Are you sure you want to remove the node below:`}</p>
          <br />
          <strong css="color: var(--pf-global--danger-color--100)">
            {nodeToDelete.unifiedJobTemplate.name}
          </strong>
        </>
      ) : (
        <p>{t`Are you sure you want to remove this node?`}</p>
      )}
    </AlertModal>
  );
}

export default NodeDeleteModal;
