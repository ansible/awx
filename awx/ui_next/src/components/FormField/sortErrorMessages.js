export default function sortErrorMessages(error, formValues = {}) {
  if (!error) {
    return {};
  }

  if (
    error?.response?.data &&
    typeof error.response.data === 'object' &&
    Object.keys(error.response.data).length > 0
  ) {
    const parsed = parseFieldErrors(error.response.data, formValues);
    return {
      formError: parsed.formErrors.join('; '),
      fieldErrors: Object.keys(parsed.fieldErrors).length
        ? parsed.fieldErrors
        : null,
    };
  }
  /* eslint-disable-next-line no-console */
  console.error(error);
  return {
    formError: error.message,
    fieldErrors: null,
  };
}

// Recursively traverse field errors object and build up field/form errors
function parseFieldErrors(obj, formValues) {
  let fieldErrors = {};
  let formErrors = [];
  Object.keys(obj).forEach(key => {
    const value = obj[key];
    if (typeof value === 'string') {
      if (typeof formValues[key] === 'undefined') {
        formErrors.push(value);
      } else {
        fieldErrors[key] = value;
      }
    } else if (Array.isArray(value)) {
      if (typeof formValues[key] === 'undefined') {
        formErrors = formErrors.concat(value);
      } else {
        fieldErrors[key] = value.join('; ');
      }
    } else if (typeof value === 'object') {
      const parsed = parseFieldErrors(value, formValues[key] || {});
      if (Object.keys(parsed.fieldErrors).length) {
        fieldErrors = {
          ...fieldErrors,
          [key]: parsed.fieldErrors,
        };
      }
      formErrors = formErrors.concat(parsed.formErrors);
    }
  });

  return { fieldErrors, formErrors };
}
