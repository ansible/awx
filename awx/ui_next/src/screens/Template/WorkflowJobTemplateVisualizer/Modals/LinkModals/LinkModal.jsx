import React, { useContext, useState } from 'react';
import { Button, FormGroup, Modal } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func } from 'prop-types';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import AnsibleSelect from '../../../../../components/AnsibleSelect';

function LinkModal({ header, i18n, onConfirm }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const { linkToEdit } = useContext(WorkflowStateContext);
  const [linkType, setLinkType] = useState(
    linkToEdit ? linkToEdit.linkType : 'success'
  );
  return (
    <Modal
      width={600}
      header={header}
      isOpen
      title={i18n._(t`Workflow Link`)}
      aria-label={i18n._(t`Workflow link modal`)}
      onClose={() => dispatch({ type: 'CANCEL_LINK_MODAL' })}
      actions={[
        <Button
          id="link-confirm"
          key="save"
          variant="primary"
          aria-label={i18n._(t`Save link changes`)}
          onClick={() => onConfirm(linkType)}
        >
          {i18n._(t`Save`)}
        </Button>,
        <Button
          id="link-cancel"
          key="cancel"
          variant="secondary"
          aria-label={i18n._(t`Cancel link changes`)}
          onClick={() => dispatch({ type: 'CANCEL_LINK_MODAL' })}
        >
          {i18n._(t`Cancel`)}
        </Button>,
      ]}
    >
      <FormGroup fieldId="link-select" label={i18n._(t`Run`)}>
        <AnsibleSelect
          id="link-select"
          name="linkType"
          value={linkType}
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
            setLinkType(value);
          }}
        />
      </FormGroup>
    </Modal>
  );
}

LinkModal.propTypes = {
  onConfirm: func.isRequired,
};

export default withI18n()(LinkModal);
