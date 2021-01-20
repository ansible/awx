import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import NodeTypeStep from './NodeTypeStep';
import StepName from '../../../../../../components/LaunchPrompt/steps/StepName';

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
    hasError: !!meta.error,
    setTouched: setFieldTouched => {
      setFieldTouched('nodeType', true, false);
    },
    validate: () => {},
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
    name: (
      <StepName hasErrors={false} id="node-type-step">
        {i18n._(t`Node type`)}
      </StepName>
    ),
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
