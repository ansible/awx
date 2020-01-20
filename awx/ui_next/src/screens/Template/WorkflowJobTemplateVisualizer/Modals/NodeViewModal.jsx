import React from 'react';
import { Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';

function NodeViewModal({ i18n, onClose, node }) {
  return (
    <Modal
      isLarge
      isOpen
      title={i18n._(t`Node Details | ${node.unifiedJobTemplate.name}`)}
      onClose={onClose}
    >
      Coming soon :)
    </Modal>
  );
}

NodeViewModal.propTypes = {
  node: shape().isRequired,
  onClose: func.isRequired,
};

export default withI18n()(NodeViewModal);
