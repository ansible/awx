import React from 'react';

import { t } from '@lingui/macro';

function LookupErrorMessage({ error }) {
  if (!error) {
    return null;
  }

  return (
    <div className="pf-c-form__helper-text pf-m-error" aria-live="polite">
      {error.message || t`An error occurred`}
    </div>
  );
}

export default LookupErrorMessage;
