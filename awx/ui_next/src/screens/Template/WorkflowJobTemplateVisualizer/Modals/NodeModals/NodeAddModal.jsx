import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import NodeModal from './NodeModal';

function NodeAddModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { addNodeSource } = useContext(WorkflowStateContext);

  const addNode = (resource, linkType) => {
    dispatch({
      type: 'CREATE_NODE',
      node: {
        linkType,
        nodeResource: resource,
      },
    });
  };

  return (
    <NodeModal
      askLinkType={addNodeSource !== 1}
      onSave={addNode}
      title={i18n._(t`Add Node`)}
    />
  );
}

export default withI18n()(NodeAddModal);
