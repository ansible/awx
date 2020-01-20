import React, { useState } from 'react';
import { Button, FormGroup, Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, node, string } from 'prop-types';
import AnsibleSelect from '@components/AnsibleSelect';

function LinkModal({ linkType, header, i18n, onCancel, onConfirm }) {
  const [newLinkType, setNewLinkType] = useState(linkType);
  return (
    <Modal
      width={600}
      header={header}
      isOpen
      title={i18n._(t`Workflow Link`)}
      onClose={onCancel}
      actions={[
        <Button
          key="save"
          variant="primary"
          aria-label={i18n._(t`Save link changes`)}
          onClick={() => onConfirm(newLinkType)}
        >
          {i18n._(t`Save`)}
        </Button>,
        <Button
          key="cancel"
          variant="secondary"
          aria-label={i18n._(t`Cancel link changes`)}
          onClick={onCancel}
        >
          {i18n._(t`Cancel`)}
        </Button>,
      ]}
    >
      <FormGroup fieldId="link-select" label={i18n._(t`Run`)}>
        <AnsibleSelect
          id="link-select"
          value={newLinkType}
          data={[
            {
              value: 'always',
              key: 'always',
              label: i18n._(t`Always`),
            },
            {
              value: 'success',
              key: 'success',
              label: i18n._(t`On Success`),
            },
            {
              value: 'failure',
              key: 'failure',
              label: i18n._(t`On Failure`),
            },
          ]}
          onChange={(event, value) => {
            setNewLinkType(value);
          }}
        />
      </FormGroup>
    </Modal>
  );
}

LinkModal.propTypes = {
  linkType: string,
  header: node.isRequired,
  onCancel: func.isRequired,
  onConfirm: func.isRequired,
};

LinkModal.defaultProps = {
  linkType: 'success',
};

export default withI18n()(LinkModal);
