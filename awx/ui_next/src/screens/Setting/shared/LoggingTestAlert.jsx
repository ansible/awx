import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
import {
  Alert,
  AlertActionCloseButton,
  AlertGroup,
} from '@patternfly/react-core';

function LoggingTestAlert({ i18n, successResponse, errorResponse, onClose }) {
  let testMessage = null;
  if (successResponse) {
    testMessage = i18n._(t`Log aggregator test sent successfully.`);
  }

  let errorData = null;
  if (errorResponse) {
    testMessage = i18n._(t`There was an error testing the log aggregator.`);
    if (
      errorResponse?.response?.statusText &&
      errorResponse?.response?.status
    ) {
      testMessage = i18n._(
        t`${errorResponse.response.statusText}: ${errorResponse.response.status}`
      );
      errorData = i18n._(t`${errorResponse.response?.data?.error}`);
    }
  }

  return (
    <AlertGroup isToast>
      {testMessage && (
        <Alert
          actionClose={<AlertActionCloseButton onClose={onClose} />}
          ouiaId="logging-test-alert"
          title={successResponse ? i18n._(t`Success`) : i18n._(t`Error`)}
          variant={successResponse ? 'success' : 'danger'}
        >
          <b id="test-message">{testMessage}</b>
          <p id="test-error">{errorData}</p>
        </Alert>
      )}
    </AlertGroup>
  );
}

LoggingTestAlert.propTypes = {
  successResponse: shape({}),
  errorResponse: shape({}),
  onClose: func,
};

LoggingTestAlert.defaultProps = {
  successResponse: null,
  errorResponse: null,
  onClose: () => {},
};

export default withI18n()(LoggingTestAlert);
