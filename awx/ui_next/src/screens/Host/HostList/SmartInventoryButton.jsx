import React from 'react';
import { func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useKebabifiedMenu } from '../../../contexts/Kebabified';

function SmartInventoryButton({ onClick, i18n, isDisabled }) {
  const { isKebabified } = useKebabifiedMenu();

  if (isKebabified) {
    return (
      <DropdownItem
        key="add"
        isDisabled={isDisabled}
        component="button"
        onClick={onClick}
      >
        {i18n._(t`Smart Inventory`)}
      </DropdownItem>
    );
  }

  return (
    <Tooltip
      key="smartInventory"
      content={
        !isDisabled
          ? i18n._(t`Create a new Smart Inventory with the applied filter`)
          : i18n._(
              t`Enter at least one search filter to create a new Smart Inventory`
            )
      }
      position="top"
    >
      <div>
        <Button
          onClick={onClick}
          aria-label={i18n._(t`Smart Inventory`)}
          variant="secondary"
          isDisabled={isDisabled}
        >
          {i18n._(t`Smart Inventory`)}
        </Button>
      </div>
    </Tooltip>
  );
}
SmartInventoryButton.propTypes = {
  onClick: func.isRequired,
};

export default withI18n()(SmartInventoryButton);
