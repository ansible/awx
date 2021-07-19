import React, { useContext, useState } from 'react';
import { Button, FormGroup, Modal } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import { func } from 'prop-types';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import AnsibleSelect from 'components/AnsibleSelect';

function LinkModal({ header, onConfirm }) {
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
      title={t`Workflow Link`}
      aria-label={t`Workflow link modal`}
      onClose={() => dispatch({ type: 'CANCEL_LINK_MODAL' })}
      actions={[
        <Button
          ouiaId="link-confirm-button"
          id="link-confirm"
          key="save"
          variant="primary"
          aria-label={t`Save link changes`}
          onClick={() => onConfirm(linkType)}
        >
          {t`Save`}
        </Button>,
        <Button
          ouiaId="link-cancel-button"
          id="link-cancel"
          key="cancel"
          variant="link"
          aria-label={t`Cancel link changes`}
          onClick={() => dispatch({ type: 'CANCEL_LINK_MODAL' })}
        >
          {t`Cancel`}
        </Button>,
      ]}
    >
      <FormGroup fieldId="link-select" label={t`Run`}>
        <AnsibleSelect
          id="link-select"
          name="linkType"
          value={linkType}
          data={[
            {
              value: 'always',
              key: 'always',
              label: t`Always`,
            },
            {
              value: 'success',
              key: 'success',
              label: t`On Success`,
            },
            {
              value: 'failure',
              key: 'failure',
              label: t`On Failure`,
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

export default LinkModal;
