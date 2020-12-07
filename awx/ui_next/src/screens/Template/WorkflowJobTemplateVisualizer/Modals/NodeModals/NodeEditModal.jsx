import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from '../../../../../contexts/Workflow';
import NodeModal from './NodeModal';

function NodeEditModal({ i18n }) {
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
      ...rest
    } = values;
    let node;
    if (values.nodeType === 'workflow_approval_template') {
      node = {
        nodeResource: {
          description: approvalDescription,
          name: approvalName,
          timeout: Number(timeoutMinutes) * 60 + Number(timeoutSeconds),
          type: 'workflow_approval_template',
        },
      };
    } else {
      node = {
        nodeResource,
      };
      if (nodeType === 'job_template' || nodeType === 'workflow_job_template') {
        node.promptValues = {
          ...rest,
          credentials,
        };

        node.launchConfig = config;
      }
    }

    dispatch({
      type: 'UPDATE_NODE',
      node,
    });
  };

  return (
    <NodeModal
      askLinkType={false}
      onSave={updateNode}
      title={i18n._(t`Edit Node`)}
    />
  );
}

export default withI18n()(NodeEditModal);
