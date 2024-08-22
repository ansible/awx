import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { Alert } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../FormLayout';
import sortErrorMessages from './sortErrorMessages';

function FormSubmitError({ error }) {
  const [errorMessage, setErrorMessage] = useState(null);
  const [fieldError, setFieldsMessage] = useState(null);
  const { values, setErrors } = useFormikContext();

  useEffect(() => {
    const { formError, fieldErrors } = sortErrorMessages(error, values);
    if (formError) {
      setErrorMessage(formError);
    }
    if (fieldErrors) {
      setErrors(fieldErrors);
      setFieldsMessage(fieldErrors);
    }
  }, [error, setErrors, values]);

  if (!errorMessage) {
    return null;
  }

  return (
    <FormFullWidthLayout>
      <Alert
        variant="danger"
        isInline
        ouiaId="form-submit-error-alert"
        title={
          Array.isArray(errorMessage)
            ? errorMessage.map((msg) => (
                <div key={msg}>
                  {msg.messages ? msg.messages : JSON.stringify(msg)}
                </div>
              ))
            : errorMessage && (
                <div>
                  {errorMessage.messages
                    ? errorMessage.messages
                    : JSON.stringify(errorMessage)}
                </div>
              )
        }
      >
        {Array.isArray(fieldError)
          ? fieldError.map((msg) => (
              <div key={msg}>
                {msg.messages ? msg.messages : JSON.stringify(msg)}
              </div>
            ))
          : fieldError && (
              <div>
                {fieldError.messages
                  ? fieldError.messages
                  : JSON.stringify(fieldError)}
              </div>
            )}
      </Alert>
    </FormFullWidthLayout>
  );
}

export default FormSubmitError;
