import React from 'react';

function LookupErrorMessage({ error }) {
  if (!error) {
    return null;
  }

  return (
    <div className="pf-c-form__helper-text pf-m-error" aria-live="polite">
      {error.message || 'An error occured'}
    </div>
  );
}

export default LookupErrorMessage;
