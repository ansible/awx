/* eslint-disable react/jsx-no-useless-fragment */
import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import { oneOf } from 'prop-types';
import { Label, Tooltip } from '@patternfly/react-core';
import icons from '../StatusIcon/icons';

const colors = {
  approved: 'green',
  denied: 'red',
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
  timedOut: 'red',
  waiting: 'grey',
  disabled: 'grey',
  canceled: 'orange',
  changed: 'orange',
};

export default function StatusLabel({ status, tooltipContent = '', children }) {
  const upperCaseStatus = {
    approved: t`Approved`,
    denied: t`Denied`,
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
    timedOut: t`Timed out`,
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
      {children || label}
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
    'approved',
    'denied',
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
    'timedOut',
    'waiting',
    'disabled',
    'canceled',
    'changed',
  ]).isRequired,
};
