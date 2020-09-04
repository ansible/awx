import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { Alert } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../FormLayout';

const findErrorStrings = (obj, messages = []) => {
  if (typeof obj === 'string') {
    messages.push(obj);
  } else if (typeof obj === 'object') {
    Object.keys(obj).forEach(key => {
      const value = obj[key];
      if (typeof value === 'string') {
        messages.push(value);
      } else if (Array.isArray(value)) {
        value.forEach(arrValue => {
          messages = findErrorStrings(arrValue, messages);
        });
      } else if (typeof value === 'object') {
        messages = findErrorStrings(value, messages);
      }
    });
  }
  return messages;
};

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
      const errorMessages = {};
      Object.keys(error.response.data).forEach(fieldName => {
        const errors = error.response.data[fieldName];
        if (errors && errors.length) {
          errorMessages[fieldName] = errors.join(' ');
        }
      });
      setErrors(errorMessages);

      const messages = findErrorStrings(error.response.data);
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
    <FormFullWidthLayout>
      <Alert
        variant="danger"
        isInline
        title={
          Array.isArray(errorMessage)
            ? errorMessage.map(msg => <div key={msg}>{msg}</div>)
            : errorMessage
        }
      />
    </FormFullWidthLayout>
  );
}

export default FormSubmitError;
