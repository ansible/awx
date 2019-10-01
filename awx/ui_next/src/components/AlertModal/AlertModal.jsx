import React from 'react';

import { Modal } from '@patternfly/react-core';

import {
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InfoCircleIcon,
  CheckCircleIcon,
} from '@patternfly/react-icons';

const getIcon = variant => {
  let icon;
  if (variant === 'warning') {
    icon = <ExclamationTriangleIcon className="at-c-alertModal__icon" />;
  } else if (variant === 'danger') {
    icon = <ExclamationCircleIcon className="at-c-alertModal__icon" />;
  }
  if (variant === 'info') {
    icon = <InfoCircleIcon className="at-c-alertModal__icon" />;
  }
  if (variant === 'success') {
    icon = <CheckCircleIcon className="at-c-alertModal__icon" />;
  }
  return icon;
};

export default ({ variant, children, ...props }) => {
  const { isOpen = null } = props;
  props.isOpen = Boolean(isOpen);
  return (
    <Modal
      className={`awx-c-modal${variant &&
        ` at-c-alertModal at-c-alertModal--${variant}`}`}
      {...props}
    >
      {children}
      {getIcon(variant)}
    </Modal>
  );
};
