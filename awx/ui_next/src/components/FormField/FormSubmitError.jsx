import React, { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import ErrorDetail from '@components/ErrorDetail';
import AlertModal from '@components/AlertModal';

function FormSubmitError({ error, i18n }) {
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
      setFormError(error);
    }
  }, [error, setErrors]);

  if (!formError) {
    return null;
  }

  return (
    <AlertModal
      variant="danger"
      title={i18n._(t`Error!`)}
      isOpen={formError}
      onClose={() => setFormError(null)}
    >
      {i18n._(t`An error occurred when saving`)}
      <ErrorDetail error={formError} />
    </AlertModal>
  );
}

export default withI18n()(FormSubmitError);
