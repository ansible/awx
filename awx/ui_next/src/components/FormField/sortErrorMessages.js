export default function sortErrorMessages(error, formValues = {}) {
  if (!error) {
    return {};
  }

  const fieldErrors = {};
  let formErrors = [];
  if (
    error?.response?.data &&
    typeof error.response.data === 'object' &&
    Object.keys(error.response.data).length > 0
  ) {
    Object.keys(error.response.data).forEach(fieldName => {
      const errors = error.response.data[fieldName];
      if (!errors) {
        return;
      }
      const errorsArray = Array.isArray(errors) ? errors : [errors];
      if (typeof formValues[fieldName] === 'undefined') {
        formErrors = [...formErrors, ...errorsArray];
      } else {
        fieldErrors[fieldName] = errorsArray.join('; ');
      }
    });
  } else {
    /* eslint-disable-next-line no-console */
    console.error(error);
    formErrors.push(error.message);
  }

  return {
    formError: formErrors.join('; '),
    fieldErrors: Object.keys(fieldErrors).length ? fieldErrors : null,
  };
}
