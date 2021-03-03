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

export default function useInventoryStep(
  launchConfig,
  resource,
  i18n,
  visitedSteps
) {
  const [, meta, helpers] = useField('inventory');
  const formError =
    !resource || resource?.type === 'workflow_job_template'
      ? false
      : Object.keys(visitedSteps).includes(STEP_ID) &&
        meta.touched &&
        !meta.value;

  return {
    step: getStep(launchConfig, i18n, formError, resource),
    initialValues: getInitialValues(launchConfig, resource),
    isReady: true,
    contentError: null,
    hasError: launchConfig.ask_inventory_on_launch && formError,
    setTouched: setFieldTouched => {
      setFieldTouched('inventory', true, false);
    },
    validate: () => {
      if (meta.touched && !meta.value && resource.type === 'job_template') {
        helpers.setError(i18n._(t`An inventory must be selected`));
      }
    },
  };
}
function getStep(launchConfig, i18n, formError, resource) {
  if (!launchConfig.ask_inventory_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    name: (
      <StepName hasErrors={formError} id="inventory-step">
        {i18n._(t`Inventory`)}
      </StepName>
    ),
    component: (
      <InventoryStep
        i18n={i18n}
        warningMessage={
          resource.type === 'workflow_job_template' ? (
            <InventoryAlert
              ouiaId="InventoryStep-alert"
              variant="warning"
              isInline
              title={i18n._(
                t`This inventory is applied to all job template nodes within this workflow (${resource.name}) that prompt for an inventory.`
              )}
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
