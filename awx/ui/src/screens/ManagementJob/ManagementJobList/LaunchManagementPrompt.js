import React, { useState } from 'react';

import { t } from '@lingui/macro';
import { Button, TextInput, Tooltip } from '@patternfly/react-core';
import { RocketIcon } from '@patternfly/react-icons';

import AlertModal from 'components/AlertModal';

const MAX_RETENTION = 99999;

const clamp = (val, min, max) => {
  if (val < min) {
    return min;
  }
  if (val > max) {
    return max;
  }
  return val;
};

function LaunchManagementPrompt({
  isOpen,
  isLoading,
  onClick,
  onClose,
  onConfirm,
  defaultDays,
}) {
  const [dataRetention, setDataRetention] = useState(defaultDays);
  return (
    <>
      <Tooltip content={t`Launch management job`} position="left">
        <Button
          aria-label={t`Launch management job`}
          variant="plain"
          onClick={onClick}
          isDisabled={isLoading}
        >
          <RocketIcon />
        </Button>
      </Tooltip>
      <AlertModal
        isOpen={isOpen}
        variant="info"
        onClose={onClose}
        title={t`Launch management job`}
        label={t`Launch management job`}
        actions={[
          <Button
            id="launch-job-confirm-button"
            key="delete"
            variant="primary"
            isDisabled={isLoading}
            aria-label={t`Launch`}
            onClick={() => onConfirm(dataRetention)}
          >
            {t`Launch`}
          </Button>,
          <Button
            id="launch-job-cancel-button"
            key="cancel"
            variant="link"
            aria-label={t`Cancel`}
            onClick={onClose}
          >
            {t`Cancel`}
          </Button>,
        ]}
      >
        {t`Set how many days of data should be retained.`}
        <TextInput
          value={dataRetention}
          type="number"
          onChange={(value) => setDataRetention(clamp(value, 0, MAX_RETENTION))}
          aria-label={t`Data retention period`}
        />
      </AlertModal>
    </>
  );
}

export default LaunchManagementPrompt;
