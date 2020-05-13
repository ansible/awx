import React, { useState } from 'react';
import { t } from '@lingui/macro';
import InventoryStep from './InventoryStep';
import StepName from './StepName';

const STEP_ID = 'inventory';

export default function useInventoryStep(config, resource, visitedSteps, i18n) {
  const [stepErrors, setStepErrors] = useState({});

  const validate = values => {
    if (!config.ask_inventory_on_launch) {
      return {};
    }
    const errors = {};
    if (!values.inventory) {
      errors.inventory = i18n._(t`An inventory must be selected`);
    }
    setStepErrors(errors);
    return errors;
  };

  const hasErrors = visitedSteps[STEP_ID] && Object.keys(stepErrors).length > 0;

  return {
    step: getStep(config, hasErrors, i18n),
    initialValues: getInitialValues(config, resource),
    validate,
    isReady: true,
    error: null,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        inventory: true,
      });
    },
  };
}

function getStep(config, hasErrors, i18n) {
  if (!config.ask_inventory_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    name: <StepName hasErrors={hasErrors}>{i18n._(t`Inventory`)}</StepName>,
    component: <InventoryStep i18n={i18n} />,
  };
}

function getInitialValues(config, resource) {
  if (!config.ask_inventory_on_launch) {
    return {};
  }
  return {
    inventory: resource?.summary_fields?.inventory || null,
  };
}
