import 'styled-components/macro';
import React, { Fragment, useContext } from 'react';
import { Button } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import AlertModal from '../../../../../components/AlertModal';

function NodeDeleteModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { nodeToDelete } = useContext(WorkflowStateContext);
  return (
    <AlertModal
      variant="danger"
      title={i18n._(t`Remove Node`)}
      isOpen={nodeToDelete}
      onClose={() => dispatch({ type: 'SET_NODE_TO_DELETE', value: null })}
      actions={[
        <Button
          id="confirm-node-removal"
          key="remove"
          variant="danger"
          aria-label={i18n._(t`Confirm node removal`)}
          onClick={() => dispatch({ type: 'DELETE_NODE' })}
        >
          {i18n._(t`Remove`)}
        </Button>,
        <Button
          id="cancel-node-removal"
          key="cancel"
          variant="secondary"
          aria-label={i18n._(t`Cancel node removal`)}
          onClick={() => dispatch({ type: 'SET_NODE_TO_DELETE', value: null })}
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
