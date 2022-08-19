import React, { useCallback, useState } from 'react';
import { t } from '@lingui/macro';
import { MinusCircleIcon } from '@patternfly/react-icons';
import { Button, Tooltip } from '@patternfly/react-core';
import { getJobModel } from 'util/jobs';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';

function JobCancelButton({
  errorTitle,
  title,
  showIconButton,
  errorMessage,
  buttonText,
  style = {},
  job = {},
  isDisabled,
  tooltip,
  cancelationMessage,
  onCancelWorkflow,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const { error: cancelError, request: cancelJob } = useRequest(
    useCallback(async () => {
      setIsOpen(false);
      await getJobModel(job.type).cancel(job.id);

      if (onCancelWorkflow) {
        onCancelWorkflow();
      }
    }, [job.id, job.type, onCancelWorkflow]),
    {}
  );
  const { error, dismissError: dismissCancelError } =
    useDismissableError(cancelError);

  const isAlreadyCancelled = cancelError?.response?.status === 405;
  const renderTooltip = () => {
    if (tooltip) {
      return tooltip;
    }
    return isAlreadyCancelled ? null : title;
  };
  return (
    <>
      <Tooltip content={renderTooltip()}>
        <div>
          {showIconButton ? (
            <Button
              isDisabled={isDisabled || isAlreadyCancelled}
              aria-label={title}
              ouiaId="cancel-job-button"
              onClick={() => setIsOpen(true)}
              variant="plain"
              style={style}
            >
              <MinusCircleIcon />
            </Button>
          ) : (
            <Button
              isDisabled={isDisabled || isAlreadyCancelled}
              aria-label={title}
              variant="secondary"
              ouiaId="cancel-job-button"
              onClick={() => setIsOpen(true)}
              style={style}
            >
              {buttonText || t`Cancel Job`}
            </Button>
          )}
        </div>
      </Tooltip>
      {isOpen && (
        <AlertModal
          isOpen={isOpen}
          variant="danger"
          onClose={() => setIsOpen(false)}
          title={title}
          label={title}
          actions={[
            <Button
              id="cancel-job-confirm-button"
              key="delete"
              variant="danger"
              aria-label={t`Confirm cancel job`}
              ouiaId="cancel-job-confirm-button"
              onClick={cancelJob}
            >
              {t`Confirm cancellation`}
            </Button>,
            <Button
              id="cancel-job-return-button"
              key="cancel"
              ouiaId="return"
              aria-label={t`Return`}
              variant="secondary"
              onClick={() => setIsOpen(false)}
            >
              {t`Return`}
            </Button>,
          ]}
        >
          {cancelationMessage ?? t`Are you sure you want to cancel this job?`}
        </AlertModal>
      )}
      {error && !isAlreadyCancelled && (
        <AlertModal
          isOpen={error}
          variant="danger"
          onClose={dismissCancelError}
          title={errorTitle}
          label={errorTitle}
        >
          {errorMessage}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default JobCancelButton;
