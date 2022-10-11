import React from 'react';
import { Plural, t } from '@lingui/macro';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { useKebabifiedMenu } from 'contexts/Kebabified';

function HealthCheckButton({
  isDisabled,
  onClick,
  selectedItems,
  healthCheckPending,
}) {
  const { isKebabified } = useKebabifiedMenu();

  const selectedItemsCount = selectedItems.length;

  const buildTooltip = () =>
    selectedItemsCount ? (
      <Plural
        value={selectedItemsCount}
        one="Click to run a health check on the selected instance."
        other="Click to run a health check on the selected instances."
      />
    ) : (
      t`Select an instance to run a health check.`
    );

  if (isKebabified) {
    return (
      <Tooltip data-cy="healthCheckTooltip" content={buildTooltip()}>
        <DropdownItem
          key="approve"
          isDisabled={isDisabled || !selectedItemsCount}
          component="button"
          onClick={onClick}
          ouiaId="health-check"
        >
          {t`Run health check`}
        </DropdownItem>
      </Tooltip>
    );
  }
  return (
    <Tooltip data-cy="healthCheckTooltip" content={buildTooltip()}>
      <div>
        <Button
          isDisabled={isDisabled || !selectedItemsCount}
          variant="secondary"
          ouiaId="health-check"
          onClick={onClick}
          isLoading={healthCheckPending}
          spinnerAriaLabel={t`Running health check`}
        >
          {healthCheckPending ? t`Running health check` : t`Run health check`}
        </Button>
      </div>
    </Tooltip>
  );
}

export default HealthCheckButton;
