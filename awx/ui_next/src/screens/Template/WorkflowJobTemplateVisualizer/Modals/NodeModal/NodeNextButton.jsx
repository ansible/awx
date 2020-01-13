import React, { useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

function NodeNextButton({ i18n, activeStep, onNext, triggerNext, onClick }) {
  useEffect(() => {
    if (!triggerNext) {
      return;
    }
    onNext();
  }, [triggerNext]);

  return (
    <Button
      variant="primary"
      type="submit"
      onClick={() => onClick(activeStep)}
      isDisabled={!activeStep.enableNext}
    >
      {activeStep.key === 'preview' ? i18n._(t`Save`) : i18n._(t`Next`)}
    </Button>
  );
}

export default withI18n()(NodeNextButton);
