import React, { useEffect, useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { string, shape } from 'prop-types';
import {
  Alert,
  AlertActionCloseButton,
  AlertGroup,
} from '@patternfly/react-core';

function CredentialPluginTestAlert({
  i18n,
  credentialName,
  successResponse,
  errorResponse,
}) {
  const [testMessage, setTestMessage] = useState('');
  const [testVariant, setTestVariant] = useState(false);
  useEffect(() => {
    if (errorResponse) {
      if (errorResponse?.response?.data?.inputs) {
        if (errorResponse.response.data.inputs.startsWith('HTTP')) {
          const [
            errorCode,
            errorStr,
          ] = errorResponse.response.data.inputs.split('\n');
          try {
            const errorJSON = JSON.parse(errorStr);
            setTestMessage(
              `${errorCode}${
                errorJSON?.errors[0] ? `: ${errorJSON.errors[0]}` : ''
              }`
            );
          } catch {
            setTestMessage(errorResponse.response.data.inputs);
          }
        } else {
          setTestMessage(errorResponse.response.data.inputs);
        }
      } else {
        setTestMessage(
          i18n._(
            t`Something went wrong with the request to test this credential and metadata.`
          )
        );
      }
      setTestVariant('danger');
    } else if (successResponse) {
      setTestMessage(i18n._(t`Test passed`));
      setTestVariant('success');
    }
  }, [i18n, successResponse, errorResponse]);

  return (
    <AlertGroup isToast>
      {testMessage && testVariant && (
        <Alert
          actionClose={
            <AlertActionCloseButton
              onClose={() => {
                setTestMessage(null);
                setTestVariant(null);
              }}
            />
          }
          title={
            <>
              <b id="credential-plugin-test-name">{credentialName}</b>
              <p id="credential-plugin-test-message">{testMessage}</p>
            </>
          }
          variant={testVariant}
        />
      )}
    </AlertGroup>
  );
}

CredentialPluginTestAlert.propTypes = {
  credentialName: string.isRequired,
  successResponse: shape({}),
  errorResponse: shape({}),
};

CredentialPluginTestAlert.defaultProps = {
  successResponse: null,
  errorResponse: null,
};

export default withI18n()(CredentialPluginTestAlert);
