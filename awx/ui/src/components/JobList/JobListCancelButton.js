import React, { useContext, useEffect, useState } from 'react';

import { t, Plural } from '@lingui/macro';
import { arrayOf, func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { KebabifiedContext } from 'contexts/Kebabified';
import { isJobRunning } from 'util/jobs';
import { Job } from 'types';
import AlertModal from '../AlertModal';

function cannotCancelBecausePermissions(job) {
  return (
    !job.summary_fields.user_capabilities.start && isJobRunning(job.status)
  );
}

function cannotCancelBecauseNotRunning(job) {
  return !isJobRunning(job.status);
}

function JobListCancelButton({ jobsToCancel, onCancel }) {
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const numJobsToCancel = jobsToCancel.length;

  const handleCancelJob = () => {
    onCancel();
    toggleModal();
  };

  const toggleModal = () => {
    setIsModalOpen(!isModalOpen);
  };

  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isModalOpen);
    }
  }, [isKebabified, isModalOpen, onKebabModalChange]);

  const renderTooltip = () => {
    const cannotCancelPermissions = jobsToCancel
      .filter(cannotCancelBecausePermissions)
      .map((job) => job.name);
    const cannotCancelNotRunning = jobsToCancel
      .filter(cannotCancelBecauseNotRunning)
      .map((job) => job.name);
    const numJobsUnableToCancel = cannotCancelPermissions.concat(
      cannotCancelNotRunning
    ).length;
    if (numJobsUnableToCancel > 0) {
      return (
        <div>
          {cannotCancelPermissions.length > 0 && (
            <div>
              <Plural
                value={cannotCancelPermissions.length}
                one="You do not have permission to cancel the following job:"
                other="You do not have permission to cancel the following jobs:"
              />
              {cannotCancelPermissions.map((job, i) => (
                <strong key={job}>
                  {' '}
                  {job}
                  {i !== cannotCancelPermissions.length - 1 ? ',' : ''}
                </strong>
              ))}
            </div>
          )}
          {cannotCancelNotRunning.length > 0 && (
            <div>
              <Plural
                value={cannotCancelNotRunning.length}
                one="You cannot cancel the following job because it is not running:"
                other="You cannot cancel the following jobs because they are not running:"
              />
              {cannotCancelNotRunning.map((job, i) => (
                <strong key={job}>
                  {' '}
                  {job}
                  {i !== cannotCancelNotRunning.length - 1 ? ',' : ''}
                </strong>
              ))}
            </div>
          )}
        </div>
      );
    }
    if (numJobsToCancel > 0) {
      return (
        <Plural
          value={numJobsToCancel}
          one={t`Cancel selected job`}
          other={t`Cancel selected jobs`}
        />
      );
    }
    return t`Select a job to cancel`;
  };

  const isDisabled =
    jobsToCancel.length === 0 ||
    jobsToCancel.some(cannotCancelBecausePermissions) ||
    jobsToCancel.some(cannotCancelBecauseNotRunning);
  const cancelJobText = (
    <Plural value={numJobsToCancel} one="Cancel job" other="Cancel jobs" />
  );

  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="cancel-job"
          isDisabled={isDisabled}
          component="button"
          aria-labelledby="jobs-list-cancel-button"
          onClick={toggleModal}
          ouiaId="cancel-job-dropdown-item"
        >
          {cancelJobText}
        </DropdownItem>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              id="jobs-list-cancel-button"
              ouiaId="cancel-job-button"
              variant="secondary"
              aria-labelledby="jobs-list-cancel-button"
              onClick={toggleModal}
              isDisabled={isDisabled}
            >
              {cancelJobText}
            </Button>
          </div>
        </Tooltip>
      )}
      {isModalOpen && (
        <AlertModal
          variant="danger"
          title={cancelJobText}
          isOpen={isModalOpen}
          onClose={toggleModal}
          actions={[
            <Button
              ouiaId="cancel-job-confirm-button"
              id="cancel-job-confirm-button"
              key="delete"
              variant="danger"
              aria-labelledby="cancel-job-confirm-button"
              onClick={handleCancelJob}
            >
              {cancelJobText}
            </Button>,
            <Button
              ouiaId="cancel-job-return-button"
              id="cancel-job-return-button"
              key="cancel"
              variant="secondary"
              aria-label={t`Return`}
              onClick={toggleModal}
            >
              {t`Return`}
            </Button>,
          ]}
        >
          <div>
            <Plural
              value={numJobsToCancel}
              one="This action will cancel the following job:"
              other="This action will cancel the following jobs:"
            />
          </div>
          {jobsToCancel.map((job) => (
            <span key={job.id}>
              <strong>{job.name}</strong>
              <br />
            </span>
          ))}
        </AlertModal>
      )}
    </>
  );
}

JobListCancelButton.propTypes = {
  jobsToCancel: arrayOf(Job),
  onCancel: func,
};

JobListCancelButton.defaultProps = {
  jobsToCancel: [],
  onCancel: () => {},
};

export default JobListCancelButton;
