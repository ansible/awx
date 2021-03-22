import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import NodeTypeStep from './NodeTypeStep';
import StepName from '../../../../../../components/LaunchPrompt/steps/StepName';

const STEP_ID = 'nodeType';

export default function useNodeTypeStep(launchConfig, i18n) {
  const [, meta] = useField('nodeType');
  const [approvalNameField] = useField('approvalName');
  const [nodeTypeField, ,] = useField('nodeType');
  const [nodeResourceField, nodeResourceMeta] = useField({
    name: 'nodeResource',
    validate: value => {
      if (
        value?.type === 'job_template' &&
        (!value?.project ||
          value?.project === null ||
          ((!value?.inventory || value?.inventory === null) &&
            !value?.ask_inventory_on_launch))
      ) {
        return i18n._(
          t`Job Templates with a missing inventory or project cannot be selected when creating or editing nodes.  Select another template or fix the missing fields to proceed.`
        );
      }
      return undefined;
    },
  });

  const formError = !!meta.error || !!nodeResourceMeta.error;

  return {
    step: getStep(
      i18n,
      nodeTypeField,
      approvalNameField,
      nodeResourceField,
      formError
    ),
    initialValues: getInitialValues(),
    isReady: true,
    contentError: null,
    hasError: formError,
    setTouched: setFieldTouched => {
      setFieldTouched('nodeType', true, false);
    },
    validate: () => {},
  };
}
function getStep(
  i18n,
  nodeTypeField,
  approvalNameField,
  nodeResourceField,
  formError
) {
  const isEnabled = () => {
    if (
      (nodeTypeField.value !== 'workflow_approval_template' &&
        nodeResourceField.value === null) ||
      (nodeTypeField.value === 'workflow_approval_template' &&
        approvalNameField.value === undefined) ||
      formError
    ) {
      return false;
    }
    return true;
  };
  return {
    id: STEP_ID,
    name: (
      <StepName hasErrors={formError} id="node-type-step">
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
