import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { WorkflowDispatchContext } from '../../../../../contexts/Workflow';
import { getAddedAndRemoved } from '../../../../../util/lists';
import NodeModal from './NodeModal';

function NodeEditModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);

  const updateNode = (values, linkType, config) => {
    const { added, removed } = getAddedAndRemoved(
      config?.defaults?.credentials,
      values?.credentials
    );
    if (added?.length > 0) {
      values.addedCredentals = added;
    }
    if (removed?.length > 0) {
      values.removedCredentals = removed;
    }
    values.inventory = values?.inventory?.id;
    delete values.linkType;
    const node = {
      nodeResource: values.nodeResource,
    };
    if (
      values?.nodeType === 'job_template' ||
      values?.nodeType === 'workflow_job_template'
    ) {
      node.promptValues = values;
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
