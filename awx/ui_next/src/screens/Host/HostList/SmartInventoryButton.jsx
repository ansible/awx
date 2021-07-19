import React from 'react';
import { bool, func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import { useKebabifiedMenu } from 'contexts/Kebabified';

function SmartInventoryButton({ onClick, isDisabled, hasInvalidKeys }) {
  const { isKebabified } = useKebabifiedMenu();

  const renderTooltipContent = () => {
    if (hasInvalidKeys) {
      return t`Some search modifiers like not__ and __search are not supported in Smart Inventory host filters.  Remove these to create a new Smart Inventory with this filter.`;
    }
    if (isDisabled) {
      return t`Enter at least one search filter to create a new Smart Inventory`;
    }

    return t`Create a new Smart Inventory with the applied filter`;
  };

  const renderContent = () => {
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
      <Button
        ouiaId="smart-inventory-button"
        onClick={onClick}
        aria-label={t`Smart Inventory`}
        variant="secondary"
        isDisabled={isDisabled}
      >
        {t`Smart Inventory`}
      </Button>
    );
  };

  return (
    <Tooltip
      key="smartInventory"
      content={renderTooltipContent()}
      position="top"
    >
      <div>{renderContent()}</div>
    </Tooltip>
  );
}
SmartInventoryButton.propTypes = {
  hasInvalidKeys: bool,
  isDisabled: bool,
  onClick: func.isRequired,
};

SmartInventoryButton.defaultProps = {
  hasInvalidKeys: false,
  isDisabled: false,
};

export default SmartInventoryButton;
