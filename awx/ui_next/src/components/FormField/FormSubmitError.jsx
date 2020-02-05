import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import styled from 'styled-components';

const ErrorMessage = styled('div')`
  color: var(--pf-global--danger-color--200);
  font-weight: var(--pf-global--FontWeight--bold);
`;
ErrorMessage.displayName = 'ErrorMessage';

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

  return <ErrorMessage>{formError.message}</ErrorMessage>;
}

export default FormSubmitError;
