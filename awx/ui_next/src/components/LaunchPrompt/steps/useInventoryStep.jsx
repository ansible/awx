import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import InventoryStep from './InventoryStep';
import StepName from './StepName';

const STEP_ID = 'inventory';

export default function useInventoryStep(
  launchConfig,
  resource,
  i18n,
  visitedSteps
) {
  const [, meta] = useField('inventory');
  const formError =
    Object.keys(visitedSteps).includes(STEP_ID) && (!meta.value || meta.error);

  return {
    step: getStep(launchConfig, i18n, formError),
    initialValues: getInitialValues(launchConfig, resource),
    isReady: true,
    contentError: null,
    formError: launchConfig.ask_inventory_on_launch && formError,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        inventory: true,
      });
    },
  };
}
function getStep(launchConfig, i18n, formError) {
  if (!launchConfig.ask_inventory_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    name: <StepName hasErrors={formError}>{i18n._(t`Inventory`)}</StepName>,
    component: <InventoryStep i18n={i18n} />,
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
