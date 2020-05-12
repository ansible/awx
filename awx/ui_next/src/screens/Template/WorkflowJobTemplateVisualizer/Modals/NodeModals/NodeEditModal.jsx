import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from '../../../../../contexts/Workflow';
import NodeModal from './NodeModal';

function NodeEditModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);

  const updateNode = resource => {
    dispatch({
      type: 'UPDATE_NODE',
      node: {
        nodeResource: resource,
      },
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
