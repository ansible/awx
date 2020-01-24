import React from 'react';
import { Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func } from 'prop-types';

function NodeViewModal({ i18n, onClose }) {
  return (
    <Modal isLarge isOpen title={i18n._(t`Node Details`)} onClose={onClose}>
      Coming soon :)
    </Modal>
  );
}

NodeViewModal.propTypes = {
  onClose: func.isRequired,
};

export default withI18n()(NodeViewModal);
