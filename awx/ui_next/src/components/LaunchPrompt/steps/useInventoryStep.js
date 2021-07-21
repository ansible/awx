import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import styled from 'styled-components';
import { Alert } from '@patternfly/react-core';
import InventoryStep from './InventoryStep';
import StepName from './StepName';

const InventoryAlert = styled(Alert)`
  margin-bottom: 16px;
`;

const STEP_ID = 'inventory';

export default function useInventoryStep(launchConfig, resource, visitedSteps) {
  const [, meta, helpers] = useField('inventory');
  const formError =
    !resource || resource?.type === 'workflow_job_template'
      ? false
      : Object.keys(visitedSteps).includes(STEP_ID) &&
        meta.touched &&
        !meta.value;

  return {
    step: getStep(launchConfig, formError, resource),
    initialValues: getInitialValues(launchConfig, resource),
    isReady: true,
    contentError: null,
    hasError: launchConfig.ask_inventory_on_launch && formError,
    setTouched: (setFieldTouched) => {
      setFieldTouched('inventory', true, false);
    },
    validate: () => {
      if (meta.touched && !meta.value && resource.type === 'job_template') {
        helpers.setError(t`An inventory must be selected`);
      }
    },
  };
}
function getStep(launchConfig, formError, resource) {
  if (!launchConfig.ask_inventory_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    name: (
      <StepName hasErrors={formError} id="inventory-step">
        {t`Inventory`}
      </StepName>
    ),
    component: (
      <InventoryStep
        warningMessage={
          resource.type === 'workflow_job_template' ? (
            <InventoryAlert
              ouiaId="InventoryStep-alert"
              variant="warning"
              isInline
              title={t`This inventory is applied to all workflow nodes within this workflow (${resource.name}) that prompt for an inventory.`}
            />
          ) : null
        }
      />
    ),
    enableNext: true,
  };
}

function getInitialValues(launchConfig, resource) {
  if (!launchConfig.ask_inventory_on_launch) {
    return {};
  }

  return {
    inventory: resource?.summary_fields?.inventory || null,
  };
}
