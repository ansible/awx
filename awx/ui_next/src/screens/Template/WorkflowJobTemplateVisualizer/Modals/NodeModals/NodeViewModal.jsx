import React, { useContext } from 'react';
import { WorkflowDispatchContext } from '@contexts/Workflow';
import { Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

function NodeViewModal({ i18n }) {
  const dispatch = useContext(WorkflowDispatchContext);
  return (
    <Modal
      isLarge
      isOpen
      isFooterLeftAligned
      title={i18n._(t`Node Details`)}
      onClose={() => dispatch({ type: 'SET_NODE_TO_VIEW', value: null })}
    >
      Coming soon :)
    </Modal>
  );
}

export default withI18n()(NodeViewModal);
