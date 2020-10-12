import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import NodeTypeStep from './NodeTypeStep';

const STEP_ID = 'nodeType';

export default function useNodeTypeStep(i18n, resource) {
  const [, meta] = useField('nodeType');
  const [approvalNameField] = useField('approvalName');
  const [nodeTypeField, ,] = useField('nodeType');
  const [nodeResouceField] = useField('nodeResource');

  return {
    step: getStep(
      meta,
      i18n,
      nodeTypeField,
      approvalNameField,
      nodeResouceField
    ),
    initialValues: getInitialValues(resource),
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
function getStep(
  meta,
  i18n,
  nodeTypeField,
  approvalNameField,
  nodeResouceField
) {
  const isEnabled = () => {
    if (
      (nodeTypeField.value !== 'approval' && nodeResouceField.value === null) ||
      (nodeTypeField.value === 'approval' &&
        approvalNameField.value === undefined)
    ) {
      return false;
    }
    return true;
  };
  return {
    id: STEP_ID,
    key: 3,
    name: i18n._(t`Node Type`),
    component: <NodeTypeStep i18n={i18n} />,
    enableNext: isEnabled(),
  };
}

function getInitialValues(resource) {
  let typeOfNode;
  if (
    !resource?.unifiedJobTemplate?.type &&
    !resource?.unifiedJobTemplate?.unified_job_type
  ) {
    return { nodeType: 'job_template' };
  }
  const {
    unifiedJobTemplate: { type, unified_job_type },
  } = resource;
  const unifiedType = type || unified_job_type;

  if (unifiedType === 'job' || unifiedType === 'job_template')
    typeOfNode = {
      nodeType: 'job_template',
      nodeResource:
        resource.originalNodeObject.summary_fields.unified_job_template,
    };
  if (unifiedType === 'project' || unifiedType === 'project_update') {
    typeOfNode = { nodeType: 'project_sync' };
  }
  if (
    unifiedType === 'inventory_source' ||
    unifiedType === 'inventory_update'
  ) {
    typeOfNode = { nodeType: 'inventory_source_sync' };
  }
  if (
    unifiedType === 'workflow_job' ||
    unifiedType === 'workflow_job_template'
  ) {
    typeOfNode = { nodeType: 'workflow_job_template' };
  }
  if (
    unifiedType === 'workflow_approval_template' ||
    unifiedType === 'workflow_approval'
  ) {
    typeOfNode = {
      nodeType: 'approval',
    };
  }
  return typeOfNode;
}
