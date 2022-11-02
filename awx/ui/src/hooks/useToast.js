import React, { useState, useCallback } from 'react';
import {
  AlertGroup,
  Alert,
  AlertActionCloseButton,
  AlertVariant,
} from '@patternfly/react-core';
import { arrayOf, func } from 'prop-types';
import { Toast as ToastType } from 'types';

export default function useToast() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((newToast) => {
    setToasts((oldToasts) => [...oldToasts, newToast]);
  }, []);

  const removeToast = useCallback((toastId) => {
    setToasts((oldToasts) => oldToasts.filter((t) => t.id !== toastId));
  }, []);

  return {
    addToast,
    removeToast,
    Toast,
    toastProps: {
      toasts,
      removeToast,
    },
  };
}

export function Toast({ toasts, removeToast }) {
  if (!toasts.length) {
    return null;
  }

  return (
    <AlertGroup data-cy="toast-container" isToast>
      {toasts.map((toast) => (
        <Alert
          actionClose={
            <AlertActionCloseButton onClose={() => removeToast(toast.id)} />
          }
          onTimeout={() => removeToast(toast.id)}
          timeout={toast.hasTimeout}
          title={toast.title}
          variant={toast.variant}
          key={`toast-message-${toast.id}`}
          ouiaId={`toast-message-${toast.id}`}
        >
          {toast.message}
        </Alert>
      ))}
    </AlertGroup>
  );
}

Toast.propTypes = {
  toasts: arrayOf(ToastType).isRequired,
  removeToast: func.isRequired,
};

export { AlertVariant };
