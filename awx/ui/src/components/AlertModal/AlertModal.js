import 'styled-components/macro';
import React from 'react';
import { Modal, Title } from '@patternfly/react-core';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InfoCircleIcon,
  TimesCircleIcon,
} from '@patternfly/react-icons';

import { t } from '@lingui/macro';
import styled from 'styled-components';

const Header = styled.div`
  display: flex;
  svg {
    margin-right: 16px;
  }
`;

function AlertModal({
  isOpen = null,
  title,
  label,
  variant,
  children,
  ...props
}) {
  const variantIcons = {
    danger: (
      <ExclamationCircleIcon
        size="lg"
        css="color: var(--pf-global--danger-color--100)"
      />
    ),
    error: (
      <TimesCircleIcon
        size="lg"
        css="color: var(--pf-global--danger-color--100)"
      />
    ),
    info: (
      <InfoCircleIcon
        size="lg"
        css="color: var(--pf-global--info-color--100)"
      />
    ),
    success: (
      <CheckCircleIcon
        size="lg"
        css="color: var(--pf-global--success-color--100)"
      />
    ),
    warning: (
      <ExclamationTriangleIcon
        size="lg"
        css="color: var(--pf-global--warning-color--100)"
      />
    ),
  };

  const customHeader = (
    <Header>
      {variant ? variantIcons[variant] : null}
      <Title id="alert-modal-header-label" size="2xl" headingLevel="h2">
        {title}
      </Title>
    </Header>
  );

  return (
    <Modal
      header={customHeader}
      aria-label={label || t`Alert modal`}
      aria-labelledby="alert-modal-header-label"
      isOpen={Boolean(isOpen)}
      variant="small"
      title={title}
      ouiaId="alert-modal"
      {...props}
    >
      {children}
    </Modal>
  );
}

export default AlertModal;
