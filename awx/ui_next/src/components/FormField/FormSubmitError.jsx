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
    if (error?.response?.data && typeof error.response.data === 'object') {
      const errorMessages = error.response.data;
      setErrors(errorMessages);
      if (errorMessages.__all__) {
        setErrorMessage(errorMessages.__all__);
      } else {
        setErrorMessage(null);
      }
    } else {
      /* eslint-disable-next-line no-console */
      console.error(error);
      setErrorMessage(error.message);
    }
  }, [error, setErrors]);

  if (!errorMessage) {
    return null;
  }

  return <Alert variant="danger" isInline title={errorMessage} />;
}

export default FormSubmitError;
