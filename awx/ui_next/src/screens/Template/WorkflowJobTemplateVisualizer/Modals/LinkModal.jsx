import React, { useState } from 'react';
import { Button, Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';

function LinkModal({
  i18n,
  header,
  onCancel,
  onConfirm,
  edgeType = 'success',
}) {
  const [newEdgeType, setNewEdgeType] = useState(edgeType);
  return (
    <Modal
      width={600}
      header={header}
      isOpen={true}
      title={i18n._(t`Workflow Link`)}
      onClose={onCancel}
      actions={[
        <Button
          key="save"
          variant="primary"
          aria-label={i18n._(t`Save link changes`)}
          onClick={() => onConfirm(newEdgeType)}
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
          value={newEdgeType}
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
            setNewEdgeType(value);
          }}
        />
      </FormGroup>
    </Modal>
  );
}

export default withI18n()(LinkModal);
