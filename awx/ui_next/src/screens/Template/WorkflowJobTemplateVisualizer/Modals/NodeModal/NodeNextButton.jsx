import React, { useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button } from '@patternfly/react-core';

function NodeNextButton({
  i18n,
  activeStep,
  onNext,
  triggerNext,
  onClick,
  buttonText,
}) {
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
      {buttonText}
    </Button>
  );
}

export default withI18n()(NodeNextButton);
