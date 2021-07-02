import React, { useContext } from 'react';

import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from 'contexts/Workflow';
import NodeModal from './NodeModal';

function NodeEditModal() {
  const dispatch = useContext(WorkflowDispatchContext);

  const updateNode = (values, config) => {
    const {
      approvalName,
      approvalDescription,
      credentials,
      linkType,
      nodeResource,
      nodeType,
      timeoutMinutes,
      timeoutSeconds,
      convergence,
      identifier,
      ...rest
    } = values;
    let node;
    if (values.nodeType === 'workflow_approval_template') {
      node = {
        all_parents_must_converge: convergence === 'all',
        nodeResource: {
          description: approvalDescription,
          name: approvalName,
          timeout: Number(timeoutMinutes) * 60 + Number(timeoutSeconds),
          type: 'workflow_approval_template',
        },
        identifier,
      };
    } else {
      node = {
        nodeResource,
        all_parents_must_converge: convergence === 'all',
        identifier,
      };
      if (nodeType === 'job_template' || nodeType === 'workflow_job_template') {
        node.promptValues = {
          ...rest,
          credentials,
        };

        node.launchConfig = config;
      }
      if (nodeType === 'system_job_template') {
        node.promptValues = {
          extra_data: values?.extra_data,
        };
      }
    }

    dispatch({
      type: 'UPDATE_NODE',
      node,
    });
  };

  return (
    <NodeModal askLinkType={false} onSave={updateNode} title={t`Edit Node`} />
  );
}

export default NodeEditModal;
