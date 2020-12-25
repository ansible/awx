import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { Alert } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../FormLayout';
import sortErrorMessages from './sortErrorMessages';

function FormSubmitError({ error }) {
  const [errorMessage, setErrorMessage] = useState(null);
  const { values, setErrors } = useFormikContext();

  useEffect(() => {
    const { formError, fieldErrors } = sortErrorMessages(error, values);
    if (formError) {
      setErrorMessage(formError);
    }
    if (fieldErrors) {
      setErrors(fieldErrors);
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
