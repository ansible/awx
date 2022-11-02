import React from 'react';
import { t } from '@lingui/macro';
import { Button, Form, ActionGroup, Alert } from '@patternfly/react-core';

export default function UnsupportedScheduleForm({ schedule, handleCancel }) {
  return (
    <Form autoComplete="off">
      <Alert
        variant="danger"
        isInline
        ouiaId="form-submit-error-alert"
        title={t`This schedule uses complex rules that are not supported in the
  UI.  Please use the API to manage this schedule.`}
      />
      <b>{t`Schedule Rules`}:</b>
      <pre css="white-space: pre; font-family: var(--pf-global--FontFamily--monospace)">
        {schedule.rrule.split(' ').join('\n')}
      </pre>
      <ActionGroup>
        <Button
          ouiaId="schedule-form-cancel-button"
          aria-label={t`Cancel`}
          variant="secondary"
          type="button"
          onClick={handleCancel}
        >
          {t`Cancel`}
        </Button>
      </ActionGroup>
    </Form>
  );
}
