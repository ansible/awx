import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';

function FormSubmitError({ error }) {
  const [formError, setFormError] = useState(null);
  const { setErrors } = useFormikContext();

  useEffect(() => {
    if (!error) {
      return;
    }
    // check for field-specific errors from API
    if (error.response?.data && typeof error.response.data === 'object') {
      setErrors(error.response.data);
      setFormError(null);
    } else {
      /* eslint-disable-next-line no-console */
      console.error(error);
      setFormError(error);
    }
  }, [error, setErrors]);

  if (!formError) {
    return null;
  }

  return <span>{formError.message}</span>;
}

export default FormSubmitError;
