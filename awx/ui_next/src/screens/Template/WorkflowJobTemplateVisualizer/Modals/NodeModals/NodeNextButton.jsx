import React, { useEffect } from 'react';
import { func, oneOfType, number, shape, string } from 'prop-types';
import { Button } from '@patternfly/react-core';

function NodeNextButton({
  activeStep,
  buttonText,
  onClick,
  onNext,
  triggerNext,
  isDisabled,
}) {
  useEffect(() => {
    if (!triggerNext) {
      return;
    }
    onNext();
  }, [onNext, triggerNext]);

  return (
    <Button
      ouiaId="node-modal-next-button"
      id="next-node-modal"
      variant="primary"
      type="submit"
      onClick={() => onClick(activeStep)}
      isDisabled={isDisabled || !activeStep.enableNext}
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
  triggerNext: oneOfType([string, number]).isRequired,
};

export default NodeNextButton;
