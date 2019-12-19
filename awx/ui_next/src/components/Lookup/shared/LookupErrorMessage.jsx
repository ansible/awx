import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

function LookupErrorMessage({ error, i18n }) {
  if (!error) {
    return null;
  }

  return (
    <div className="pf-c-form__helper-text pf-m-error" aria-live="polite">
      {error.message || i18n._(t`An error occured`)}
    </div>
  );
}

export default withI18n()(LookupErrorMessage);
