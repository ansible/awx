import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { Alert } from '@patternfly/react-core';

function FormSubmitError({ error }) {
  const [errorMessage, setErrorMessage] = useState(null);
  const { setErrors } = useFormikContext();

  useEffect(() => {
    if (!error) {
      return;
    }
    if (
      error?.response?.data &&
      typeof error.response.data === 'object' &&
      Object.keys(error.response.data).length > 0
    ) {
      const errorMessages = error.response.data;
      setErrors(errorMessages);

      let messages = [];
      Object.values(error.response.data).forEach(value => {
        if (Array.isArray(value)) {
          messages = messages.concat(value);
        } else {
          messages.push(value);
        }
      });
      setErrorMessage(messages.length > 0 ? messages : null);
    } else {
      /* eslint-disable-next-line no-console */
      console.error(error);
      setErrorMessage(error.message);
    }
  }, [error, setErrors]);

  if (!errorMessage) {
    return null;
  }

  return (
    <Alert
      variant="danger"
      isInline
      title={
        Array.isArray(errorMessage)
          ? errorMessage.map(msg => <div key={msg}>{msg}</div>)
          : errorMessage
      }
    />
  );
}

export default FormSubmitError;
