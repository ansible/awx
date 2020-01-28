import React, { useContext } from 'react';
import { WorkflowDispatchContext } from '@contexts/Workflow';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import NodeModal from './NodeModal';

function NodeEditModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);

  const updateNode = (linkType, resource, nodeType) => {
    dispatch({
      type: 'UPDATE_NODE',
      node: {
        linkType,
        nodeResource: resource,
        nodeType,
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
