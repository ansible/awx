import React from 'react';
import { t } from '@lingui/macro';
import InventoryStep from './InventoryStep';

const STEP_ID = 'inventory';

export default function useInventoryStep(config, resource, i18n) {
  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, resource),
    isReady: true,
    error: null,
  };
}

function getStep(config, i18n) {
  if (!config.ask_inventory_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    name: i18n._(t`Inventory`),
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
