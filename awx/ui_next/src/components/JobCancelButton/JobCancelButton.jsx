import React, { useCallback, useState } from 'react';
import { t } from '@lingui/macro';
import { MinusCircleIcon } from '@patternfly/react-icons';
import { Button, Tooltip } from '@patternfly/react-core';
import { getJobModel } from '../../util/jobs';
import useRequest, { useDismissableError } from '../../util/useRequest';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';

function JobCancelButton({
  job = {},
  errorTitle,
  title,
  showIconButton,
  errorMessage,
  buttonText,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const { error: cancelError, request: cancelJob } = useRequest(
    useCallback(async () => {
      setIsOpen(false);
      await getJobModel(job.type).cancel(job.id);
    }, [job.id, job.type]),
    {}
  );
  const { error, dismissError: dismissCancelError } = useDismissableError(
    cancelError
  );

  return (
    <>
      <Tooltip content={title}>
        {showIconButton ? (
          <Button
            aria-label={title}
            ouiaId="cancel-job-button"
            onClick={() => setIsOpen(true)}
            variant="plain"
          >
            <MinusCircleIcon />
          </Button>
        ) : (
          <Button
            aria-label={title}
            variant="secondary"
            ouiaId="cancel-job-button"
            onClick={() => setIsOpen(true)}
          >
            {buttonText || t`Cancel Job`}
          </Button>
        )}
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
          {t`Are you sure you want to cancel this job?`}
        </AlertModal>
      )}
      {error && (
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
