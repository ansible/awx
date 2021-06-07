import React from 'react';
import { func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import { useKebabifiedMenu } from '../../../contexts/Kebabified';

function SmartInventoryButton({ onClick, isDisabled }) {
  const { isKebabified } = useKebabifiedMenu();

  if (isKebabified) {
    return (
      <DropdownItem
        key="add"
        isDisabled={isDisabled}
        component="button"
        onClick={onClick}
      >
        {t`Smart Inventory`}
      </DropdownItem>
    );
  }

  return (
    <Tooltip
      key="smartInventory"
      content={
        !isDisabled
          ? t`Create a new Smart Inventory with the applied filter`
          : t`Enter at least one search filter to create a new Smart Inventory`
      }
      position="top"
    >
      <div>
        <Button
          ouiaId="smart-inventory-button"
          onClick={onClick}
          aria-label={t`Smart Inventory`}
          variant="secondary"
          isDisabled={isDisabled}
        >
          {t`Smart Inventory`}
        </Button>
      </div>
    </Tooltip>
  );
}
SmartInventoryButton.propTypes = {
  onClick: func.isRequired,
};

export default SmartInventoryButton;
