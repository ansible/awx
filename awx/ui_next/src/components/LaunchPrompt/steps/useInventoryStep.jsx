import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import InventoryStep from './InventoryStep';
import StepName from './StepName';

const STEP_ID = 'inventory';

export default function useInventoryStep(
  config,
  i18n,
  visitedSteps,
  selectedResource,
  nodeToEdit
) {
  const [, meta] = useField('inventory');
  const resource = nodeToEdit?.originalNodeObject || nodeToEdit?.promptValues || selectedResource;
  const formError =
    Object.keys(visitedSteps).includes(STEP_ID) && (!meta.value || meta.error);

  return {
    step: getStep(config, i18n, formError),
    initialValues: getInitialValues(config, resource),
    isReady: true,
    contentError: null,
    formError: config.ask_inventory_on_launch && formError,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        inventory: true,
      });
    },
  };
}
function getStep(config, i18n, formError) {
  if (!config.ask_inventory_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 3,
    name: <StepName hasErrors={formError}>{i18n._(t`Inventory`)}</StepName>,
    component: <InventoryStep i18n={i18n} />,
    enableNext: true,
  };
}

function getInitialValues(config, resource) {
  if (!config.ask_inventory_on_launch) {
    return {};
  }

  return {
    inventory: resource?.summary_fields?.inventory || resource?.inventory || null,
  };
}
