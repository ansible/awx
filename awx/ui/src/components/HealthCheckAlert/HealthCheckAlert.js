import React from 'react';
import { t } from '@lingui/macro';
import { Alert, Button, AlertActionCloseButton } from '@patternfly/react-core';

function HealthCheckAlert({ onSetHealthCheckAlert }) {
  return (
    <Alert
      variant="default"
      actionClose={
        <AlertActionCloseButton onClose={() => onSetHealthCheckAlert(false)} />
      }
      title={
        <>
          {t`Health check request(s) submitted. Please wait and reload the page.`}{' '}
          <Button
            variant="link"
            isInline
            onClick={() => window.location.reload(false)}
          >{t`Reload`}</Button>
        </>
      }
    />
  );
}

export default HealthCheckAlert;
