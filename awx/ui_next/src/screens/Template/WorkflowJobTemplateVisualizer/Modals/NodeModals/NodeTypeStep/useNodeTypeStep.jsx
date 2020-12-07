import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import NodeTypeStep from './NodeTypeStep';

const STEP_ID = 'nodeType';

export default function useNodeTypeStep(i18n) {
  const [, meta] = useField('nodeType');
  const [approvalNameField] = useField('approvalName');
  const [nodeTypeField, ,] = useField('nodeType');
  const [nodeResourceField] = useField('nodeResource');

  return {
    step: getStep(i18n, nodeTypeField, approvalNameField, nodeResourceField),
    initialValues: getInitialValues(),
    isReady: true,
    contentError: null,
    formError: meta.error,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        inventory: true,
      });
    },
  };
}
function getStep(i18n, nodeTypeField, approvalNameField, nodeResourceField) {
  const isEnabled = () => {
    if (
      (nodeTypeField.value !== 'workflow_approval_template' &&
        nodeResourceField.value === null) ||
      (nodeTypeField.value === 'workflow_approval_template' &&
        approvalNameField.value === undefined)
    ) {
      return false;
    }
    return true;
  };
  return {
    id: STEP_ID,
    name: i18n._(t`Node Type`),
    component: <NodeTypeStep i18n={i18n} />,
    enableNext: isEnabled(),
  };
}

function getInitialValues() {
  return {
    approvalName: '',
    approvalDescription: '',
    timeoutMinutes: 0,
    timeoutSeconds: 0,
    nodeType: 'job_template',
  };
}
