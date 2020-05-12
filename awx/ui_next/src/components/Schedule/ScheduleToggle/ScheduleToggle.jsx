import 'styled-components/macro';
import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Tooltip } from '@patternfly/react-core';
import AlertModal from '../../AlertModal';
import ErrorDetail from '../../ErrorDetail';
import useRequest from '../../../util/useRequest';
import { SchedulesAPI } from '../../../api';

function ScheduleToggle({ schedule, onToggle, className, i18n }) {
  const [isEnabled, setIsEnabled] = useState(schedule.enabled);
  const [showError, setShowError] = useState(false);

  const { result, isLoading, error, request: toggleSchedule } = useRequest(
    useCallback(async () => {
      await SchedulesAPI.update(schedule.id, {
        enabled: !isEnabled,
      });
      return !isEnabled;
    }, [schedule, isEnabled]),
    schedule.enabled
  );

  useEffect(() => {
    if (result !== isEnabled) {
      setIsEnabled(result);
      if (onToggle) {
        onToggle(result);
      }
    }
  }, [result, isEnabled, onToggle]);

  useEffect(() => {
    if (error) {
      setShowError(true);
    }
  }, [error]);

  return (
    <Fragment>
      <Tooltip
        content={
          schedule.enabled
            ? i18n._(t`Schedule is active`)
            : i18n._(t`Schedule is inactive`)
        }
        position="top"
      >
        <Switch
          className={className}
          css="display: inline-flex;"
          id={`schedule-${schedule.id}-toggle`}
          label={i18n._(t`On`)}
          labelOff={i18n._(t`Off`)}
          isChecked={isEnabled}
          isDisabled={
            isLoading || !schedule.summary_fields.user_capabilities.edit
          }
          onChange={toggleSchedule}
          aria-label={i18n._(t`Toggle schedule`)}
        />
      </Tooltip>
      {showError && error && !isLoading && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={error && !isLoading}
          onClose={() => setShowError(false)}
        >
          {i18n._(t`Failed to toggle schedule.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </Fragment>
  );
}

export default withI18n()(ScheduleToggle);
