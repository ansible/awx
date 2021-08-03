import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { getAddedAndRemoved } from 'util/lists';
import NodeModal from './NodeModal';

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
      identifier,
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
      identifier,
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
      if (values?.nodeType === 'system_job_template') {
        node.promptValues = {
          extra_data: values?.extra_data,
        };
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
