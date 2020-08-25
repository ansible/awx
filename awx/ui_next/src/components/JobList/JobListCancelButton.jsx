import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { arrayOf, func } from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';
import { Kebabified } from '../../contexts/Kebabified';
import AlertModal from '../AlertModal';
import { Job } from '../../types';

function cannotCancel(job) {
  return !job.summary_fields.user_capabilities.start;
}

function JobListCancelButton({ i18n, jobsToCancel, onCancel }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCancel = () => {
    onCancel();
    setIsModalOpen(false);
  };

  const renderTooltip = () => {
    const jobsUnableToCancel = jobsToCancel
      .filter(cannotCancel)
      .map(job => job.name)
      .join(', ');
    if (jobsToCancel.some(cannotCancel)) {
      return (
        <div>
          {i18n.plural({
            value: jobsToCancel.length,
            one: 'You do not have permission to cancel the following job: ',
            other: 'You do not have permission to cancel the following jobs: ',
          })}
          {jobsUnableToCancel}
        </div>
      );
    }
    if (jobsToCancel.length) {
      return i18n.plural({
        value: jobsToCancel.length,
        one: 'Cancel selected job',
        other: 'Cancel selected jobs',
      });
    }
    return i18n._(t`Select a job to cancel`);
  };

  const isDisabled =
    jobsToCancel.length === 0 || jobsToCancel.some(cannotCancel);

  const cancelJobText = i18n.plural({
    value: jobsToCancel.length < 2,
    one: 'Cancel job',
    other: 'Cancel jobs',
  });

  return (
    <Kebabified>
      {({ isKebabified }) => (
        <>
          {isKebabified ? (
            <DropdownItem
              key="cancel-job"
              isDisabled={isDisabled}
              component="Button"
              onClick={() => setIsModalOpen(true)}
            >
              {cancelJobText}
            </DropdownItem>
          ) : (
            <Tooltip content={renderTooltip()} position="top">
              <div>
                <Button
                  variant="secondary"
                  aria-label={cancelJobText}
                  onClick={() => setIsModalOpen(true)}
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
              onClose={() => setIsModalOpen(false)}
              actions={[
                <Button
                  key="delete"
                  variant="danger"
                  aria-label={cancelJobText}
                  onClick={handleCancel}
                >
                  {cancelJobText}
                </Button>,
                <Button
                  key="cancel"
                  variant="secondary"
                  aria-label={i18n._(t`Return`)}
                  onClick={() => setIsModalOpen(false)}
                >
                  {i18n._(t`Return`)}
                </Button>,
              ]}
            >
              <div>
                {i18n.plural({
                  value: jobsToCancel.length,
                  one: 'This action will cancel the following job:',
                  other: 'This action will cancel the following jobs:',
                })}
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
      )}
    </Kebabified>
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
