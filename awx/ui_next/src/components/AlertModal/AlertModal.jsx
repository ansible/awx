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

export default ({ isOpen = null, title, variant, children, ...props }) => {
  const variantIcons = {
    danger: <ExclamationCircleIcon size="lg" css="color: #c9190b" />,
    error: <TimesCircleIcon size="lg" css="color: #c9190b" />,
    info: <InfoCircleIcon size="lg" css="color: #73bcf7" />,
    success: <CheckCircleIcon size="lg" css="color: #92d400" />,
    warning: <ExclamationTriangleIcon size="lg" css="color: #f0ab00" />,
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
};
