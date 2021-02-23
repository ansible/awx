import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Button, TextInput, Tooltip } from '@patternfly/react-core';
import { RocketIcon } from '@patternfly/react-icons';

import AlertModal from '../../../components/AlertModal';

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
  i18n,
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
      <Tooltip content={i18n._(t`Launch management job`)} position="top">
        <Button
          aria-label={i18n._(t`Launch management job`)}
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
        title={i18n._(t`Launch management job`)}
        label={i18n._(t`Launch management job`)}
        actions={[
          <Button
            id="launch-job-confirm-button"
            key="delete"
            variant="primary"
            isDisabled={isLoading}
            aria-label={i18n._(t`Launch`)}
            onClick={() => onConfirm(dataRetention)}
          >
            {i18n._(t`Launch`)}
          </Button>,
          <Button
            id="launch-job-cancel-button"
            key="cancel"
            variant="link"
            aria-label={i18n._(t`Cancel`)}
            onClick={onClose}
          >
            {i18n._(t`Cancel`)}
          </Button>,
        ]}
      >
        {i18n._(t`Set how many days of data should be retained.`)}
        <TextInput
          value={dataRetention}
          type="number"
          onChange={value => setDataRetention(clamp(value, 0, MAX_RETENTION))}
          aria-label={i18n._(t`Data retention period`)}
        />
      </AlertModal>
    </>
  );
}

export default withI18n()(LaunchManagementPrompt);
