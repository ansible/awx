import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import { oneOf } from 'prop-types';
import { Label, Tooltip } from '@patternfly/react-core';
import icons from '../StatusIcon/icons';

const colors = {
  success: 'green',
  successful: 'green',
  healthy: 'green',
  failed: 'red',
  error: 'red',
  running: 'blue',
  pending: 'blue',
  waiting: 'grey',
  disabled: 'grey',
  canceled: 'orange',
};

export default function StatusLabel({ status, tooltipContent = '' }) {
  const upperCaseStatus = {
    success: t`Success`,
    healthy: t`Healthy`,
    successful: t`Successful`,
    failed: t`Failed`,
    error: t`Error`,
    running: t`Running`,
    pending: t`Pending`,
    waiting: t`Waiting`,
    disabled: t`Disabled`,
    canceled: t`Canceled`,
  };
  const label = upperCaseStatus[status] || t`Undefined`;
  const color = colors[status] || 'grey';
  const Icon = icons[status];

  const renderLabel = () => (
    <Label variant="outline" color={color} icon={Icon ? <Icon /> : null}>
      {label}
    </Label>
  );

  return (
    <>
      {tooltipContent ? (
        <Tooltip content={tooltipContent} position="top">
          {renderLabel()}
        </Tooltip>
      ) : (
        renderLabel()
      )}
    </>
  );
}

StatusLabel.propTypes = {
  status: oneOf([
    'success',
    'successful',
    'healthy',
    'failed',
    'error',
    'running',
    'pending',
    'waiting',
    'disabled',
    'canceled',
  ]).isRequired,
};
