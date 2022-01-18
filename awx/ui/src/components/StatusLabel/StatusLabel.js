import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import { oneOf } from 'prop-types';
import { Label, Tooltip } from '@patternfly/react-core';
import icons from '../StatusIcon/icons';

const colors = {
  success: 'green',
  successful: 'green',
  ok: 'green',
  healthy: 'green',
  failed: 'red',
  error: 'red',
  unreachable: 'red',
  running: 'blue',
  pending: 'blue',
  skipped: 'blue',
  waiting: 'grey',
  disabled: 'grey',
  canceled: 'orange',
  changed: 'orange',
};

export default function StatusLabel({ status, tooltipContent = '' }) {
  const upperCaseStatus = {
    success: t`Success`,
    healthy: t`Healthy`,
    successful: t`Successful`,
    ok: t`OK`,
    failed: t`Failed`,
    error: t`Error`,
    unreachable: t`Unreachable`,
    running: t`Running`,
    pending: t`Pending`,
    skipped: t`Skipped'`,
    waiting: t`Waiting`,
    disabled: t`Disabled`,
    canceled: t`Canceled`,
    changed: t`Changed`,
  };
  const label = upperCaseStatus[status] || status;
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
    'ok',
    'healthy',
    'failed',
    'error',
    'unreachable',
    'running',
    'pending',
    'skipped',
    'waiting',
    'disabled',
    'canceled',
    'changed',
  ]).isRequired,
};
