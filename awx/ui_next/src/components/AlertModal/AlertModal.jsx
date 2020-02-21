import React from 'react';
import { Modal, Title } from '@patternfly/react-core';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InfoCircleIcon,
  TimesCircleIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';

const Header = styled.div`
  display: flex;
  svg {
    margin-right: 16px;
  }
`;

export default function AlertModal({
  isOpen = null,
  title,
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
      <Title size="2xl">{title}</Title>
    </Header>
  );

  return (
    <Modal
      header={customHeader}
      isFooterLeftAligned
      isOpen={Boolean(isOpen)}
      isSmall
      title={title}
      {...props}
    >
      {children}
    </Modal>
  );
}
