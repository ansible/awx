import React from 'react';
import { t } from '@lingui/macro';
import {
  Alert as PFAlert,
  Button,
  AlertActionCloseButton,
} from '@patternfly/react-core';
import styled from 'styled-components';

const Alert = styled(PFAlert)`
  z-index: 1;
`;
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
            onClick={() => window.location.reload()}
          >{t`Reload`}</Button>
        </>
      }
    />
  );
}

export default HealthCheckAlert;
