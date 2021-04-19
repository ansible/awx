import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import NodeModal from './NodeModal';
import { getAddedAndRemoved } from '../../../../../util/lists';

function NodeAddModal() {
  const dispatch = useContext(WorkflowDispatchContext);
  const { addNodeSource } = useContext(WorkflowStateContext);

  const addNode = (values, config) => {
    const {
      approvalName,
      approvalDescription,
      timeoutMinutes,
      timeoutSeconds,
      linkType,
      convergence,
    } = values;

    if (values) {
      const { added, removed } = getAddedAndRemoved(
        config?.defaults?.credentials,
        values?.credentials
      );

      values.addedCredentials = added;
      values.removedCredentials = removed;
    }

    const node = {
      linkType,
      all_parents_must_converge: convergence === 'all',
    };

    delete values.convergence;

    delete values.linkType;

    if (values.nodeType === 'workflow_approval_template') {
      node.nodeResource = {
        description: approvalDescription,
        name: approvalName,
        timeout: Number(timeoutMinutes) * 60 + Number(timeoutSeconds),
        type: 'workflow_approval_template',
      };
    } else {
      node.nodeResource = values.nodeResource;
      if (
        values?.nodeType === 'job_template' ||
        values?.nodeType === 'workflow_job_template'
      ) {
        node.promptValues = values;
      }
    }
    dispatch({
      type: 'CREATE_NODE',
      node,
    });
  };

  return (
    <NodeModal
      askLinkType={addNodeSource !== 1}
      onSave={addNode}
      title={t`Add Node`}
    />
  );
}

export default NodeAddModal;
