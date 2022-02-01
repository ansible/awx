import React from 'react';
import { Plural, t } from '@lingui/macro';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { useKebabifiedMenu } from 'contexts/Kebabified';

function HealthCheckButton({ isDisabled, onClick, selectedItems }) {
  const { isKebabified } = useKebabifiedMenu();
  const hopNodeSelected = selectedItems.filter(
    (instance) => instance.node_type === 'hop'
  ).length;
  const buildTooltip = () => {
    if (hopNodeSelected) {
      return (
        <Plural
          value={hopNodeSelected}
          one="Cannot run health check on a hop node.  Deselect the hop node to run a health check."
          other="Cannot run health check on hop nodes.  Deselect the hop nodes to run health checks."
        />
      );
    }
    return selectedItems.length ? (
      <Plural
        value={selectedItems.length}
        one="Click to run a health check on the selected instance."
        other="Click to run a health check on the selected instances."
      />
    ) : (
      t`Select an instance to run a health check.`
    );
  };

  if (isKebabified) {
    return (
      <Tooltip ouiaId="healthCheckTooltip" content={buildTooltip()}>
        <DropdownItem
          key="approve"
          isDisabled={isDisabled}
          component="button"
          onClick={onClick}
          ouiaId="health-check"
        >
          {t`Health Check`}
        </DropdownItem>
      </Tooltip>
    );
  }
  return (
    <Tooltip ouiaId="healthCheckTooltip" content={buildTooltip()}>
      <div>
        <Button
          isDisabled={isDisabled}
          variant="secondary"
          ouiaId="health-check"
          onClick={onClick}
        >{t`Health Check`}</Button>
      </div>
    </Tooltip>
  );
}

export default HealthCheckButton;
