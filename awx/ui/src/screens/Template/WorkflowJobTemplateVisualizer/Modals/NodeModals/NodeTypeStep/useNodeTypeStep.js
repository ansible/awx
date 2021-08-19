import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import StepName from 'components/LaunchPrompt/steps/StepName';
import { stringIsUUID } from 'util/strings';
import NodeTypeStep from './NodeTypeStep';

const STEP_ID = 'nodeType';

export default function useNodeTypeStep(nodeToEdit) {
  const [, meta] = useField('nodeType');
  const [approvalNameField] = useField('approvalName');
  const [nodeTypeField, ,] = useField('nodeType');
  const [, identifierMeta] = useField('identifier');
  const [nodeResourceField, nodeResourceMeta] = useField({
    name: 'nodeResource',
    validate: (value) => {
      if (
        value?.type === 'job_template' &&
        (!value?.project ||
          value?.project === null ||
          ((!value?.inventory || value?.inventory === null) &&
            !value?.ask_inventory_on_launch))
      ) {
        return t`Job Templates with a missing inventory or project cannot be selected when creating or editing nodes.  Select another template or fix the missing fields to proceed.`;
      }
      return undefined;
    },
  });

  const formError =
    !!meta.error || !!nodeResourceMeta.error || identifierMeta.error;

  return {
    step: getStep(
      nodeTypeField,
      approvalNameField,
      nodeResourceField,
      formError,
      nodeToEdit
    ),
    initialValues: getInitialValues(),
    isReady: true,
    contentError: null,
    hasError: formError,
    setTouched: (setFieldTouched) => {
      setFieldTouched('nodeType', true, false);
    },
    validate: () => {},
  };
}
function getStep(
  nodeTypeField,
  approvalNameField,
  nodeResourceField,
  formError,
  nodeToEdit
) {
  const isEnabled = () => {
    if (
      (nodeTypeField.value !== 'workflow_approval_template' &&
        nodeResourceField.value === null) ||
      (nodeTypeField.value === 'workflow_approval_template' &&
        approvalNameField.value === '') ||
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
        {t`Node type`}
      </StepName>
    ),
    component: (
      <NodeTypeStep
        isIdentifierRequired={
          nodeToEdit &&
          nodeToEdit.originalNodeObject &&
          !stringIsUUID(nodeToEdit.originalNodeObject?.identifier)
        }
      />
    ),
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
    convergence: 'any',
    identifier: '',
  };
}
