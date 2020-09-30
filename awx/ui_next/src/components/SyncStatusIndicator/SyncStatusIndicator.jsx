import React from 'react';
import 'styled-components/macro';
import styled, { keyframes } from 'styled-components';
import { oneOf, string } from 'prop-types';
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

export default function SyncStatusIndicator({ status, title }) {
  const color = COLORS[status] || COLORS.disabled;

  if (status === 'syncing') {
    return (
      <>
        <PulseWrapper aria-hidden="true">
          <CloudIcon color={`var(${color})`} title={title} />
        </PulseWrapper>
        <span className="pf-screen-reader">{status}</span>
      </>
    );
  }

  return (
    <>
      <CloudIcon color={`var(${color})`} title={title} aria-hidden="true" />
      <span className="pf-screen-reader">{status}</span>
    </>
  );
}
SyncStatusIndicator.propTypes = {
  status: oneOf(['success', 'error', 'disabled', 'syncing']).isRequired,
  title: string,
};
SyncStatusIndicator.defaultProps = {
  title: null,
};
