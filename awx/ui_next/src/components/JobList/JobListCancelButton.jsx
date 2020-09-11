import React, { useContext, useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { arrayOf, func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { KebabifiedContext } from '../../contexts/Kebabified';
import AlertModal from '../AlertModal';
import { Job } from '../../types';

function cannotCancel(job) {
  return !job.summary_fields.user_capabilities.start;
}

function JobListCancelButton({ i18n, jobsToCancel, onCancel }) {
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const numJobsToCancel = jobsToCancel.length;
  const zeroOrOneJobSelected = numJobsToCancel < 2;

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
    const jobsUnableToCancel = jobsToCancel
      .filter(cannotCancel)
      .map(job => job.name);
    const numJobsUnableToCancel = jobsUnableToCancel.length;
    if (numJobsUnableToCancel > 0) {
      return (
        <div>
          {i18n._(
            '{numJobsUnableToCancel, plural, one {You do not have permission to cancel the following job:} other {You do not have permission to cancel the following jobs:}}',
            {
              numJobsUnableToCancel,
            }
          )}
          {' '.concat(jobsUnableToCancel.join(', '))}
        </div>
      );
    }
    if (numJobsToCancel > 0) {
      return i18n._(
        '{numJobsToCancel, plural, one {Cancel selected job} other {Cancel selected jobs}}',
        {
          numJobsToCancel,
        }
      );
    }
    return i18n._(t`Select a job to cancel`);
  };

  const isDisabled =
    jobsToCancel.length === 0 || jobsToCancel.some(cannotCancel);

  const cancelJobText = i18n._(
    '{zeroOrOneJobSelected, plural, one {Cancel job} other {Cancel jobs}}',
    {
      zeroOrOneJobSelected,
    }
  );

  return (
    <>
      {isKebabified ? (
        <DropdownItem
          key="cancel-job"
          isDisabled={isDisabled}
          component="button"
          onClick={toggleModal}
        >
          {cancelJobText}
        </DropdownItem>
      ) : (
        <Tooltip content={renderTooltip()} position="top">
          <div>
            <Button
              variant="secondary"
              aria-label={cancelJobText}
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
              id="cancel-job-confirm-button"
              key="delete"
              variant="danger"
              aria-label={cancelJobText}
              onClick={handleCancelJob}
            >
              {cancelJobText}
            </Button>,
            <Button
              id="cancel-job-return-button"
              key="cancel"
              variant="secondary"
              aria-label={i18n._(t`Return`)}
              onClick={toggleModal}
            >
              {i18n._(t`Return`)}
            </Button>,
          ]}
        >
          <div>
            {i18n._(
              '{numJobsToCancel, plural, one {This action will cancel the following job:} other {This action will cancel the following jobs:}}',
              {
                numJobsToCancel,
              }
            )}
          </div>
          {jobsToCancel.map(job => (
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

export default withI18n()(JobListCancelButton);
