import React, { useEffect } from 'react';
import { func, number, shape, string } from 'prop-types';
import { Button } from '@patternfly/react-core';

function NodeNextButton({
  activeStep,
  buttonText,
  onClick,
  onNext,
  triggerNext,
}) {
  useEffect(() => {
    if (!triggerNext) {
      return;
    }
    onNext();
  }, [onNext, triggerNext]);

  return (
    <Button
      id="next-node-modal"
      variant="primary"
      type="submit"
      onClick={() => onClick(activeStep)}
      isDisabled={!activeStep.enableNext}
    >
      {buttonText}
    </Button>
  );
}

NodeNextButton.propTypes = {
  activeStep: shape().isRequired,
  buttonText: string.isRequired,
  onClick: func.isRequired,
  onNext: func.isRequired,
  triggerNext: number.isRequired,
};

export default NodeNextButton;
