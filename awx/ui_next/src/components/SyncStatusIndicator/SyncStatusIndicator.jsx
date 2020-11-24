import React, { useRef } from 'react';
import 'styled-components/macro';
import { Tooltip } from '@patternfly/react-core';
import styled, { keyframes } from 'styled-components';
import { oneOf, shape, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CloudIcon } from '@patternfly/react-icons';

const COLORS = {
  success: '--pf-global--palette--green-400',
  syncing: '--pf-global--palette--green-400',
  error: '--pf-global--danger-color--100',
  disabled: '--pf-global--disabled-color--200',
};

const Pulse = keyframes`
  from {
    opacity: 0;
  }
  to {
    opacity: 1.0;
  }
`;

const PulseWrapper = styled.div`
  animation: ${Pulse} 1.5s linear infinite alternate;
`;

function SyncStatusIndicator({ inventory, status, title, i18n }) {
  const color = COLORS[status] || COLORS.disabled;
  const tooltipRef = useRef();
  const otherRef = useRef();
  if (status === 'syncing') {
    return (
      <>
        <Tooltip
          content={i18n._(t`Syncing`)}
          position="top"
          reference={tooltipRef}
        />
        <PulseWrapper aria-hidden="true" ref={tooltipRef}>
          <CloudIcon color={`var(${color})`} title={title} />
        </PulseWrapper>
        <span className="pf-screen-reader">{status}</span>
      </>
    );
  }
  let tooltipContent = '';
  if (inventory.has_inventory_sources) {
    if (inventory.inventory_sources_with_failures > 0) {
      tooltipContent = i18n._(
        t`${inventory.inventory_sources_with_failures} sources with sync failures.`
      );
    } else {
      tooltipContent = i18n._(t`No inventory sync failures.`);
    }
  } else {
    tooltipContent = i18n._(t`Not configured for inventory sync.`);
  }
  return (
    <>
      <Tooltip content={tooltipContent} position="top" reference={otherRef} />
      <div ref={otherRef} aria-hidden="true">
        <CloudIcon color={`var(${color})`} title={title} ref={otherRef} />
      </div>
      <span className="pf-screen-reader">{status}</span>
    </>
  );
}

SyncStatusIndicator.propTypes = {
  status: oneOf(['success', 'error', 'disabled', 'syncing']).isRequired,
  title: string,
  inventory: shape({}).isRequired,
};

SyncStatusIndicator.defaultProps = {
  title: null,
};

export default withI18n()(SyncStatusIndicator);
