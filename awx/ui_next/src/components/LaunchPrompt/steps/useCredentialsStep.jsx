import React from 'react';
import { t } from '@lingui/macro';
import CredentialsStep from './CredentialsStep';

const STEP_ID = 'credentials';

export default function useCredentialsStep(
  config,
  i18n,
  loadedResource,
  currentResource
) {
  const validate = () => {
    return {};
  };

  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, loadedResource, currentResource),
    validate,
    isReady: true,
    contentError: null,
    formError: null,
    setTouched: setFieldsTouched => {
      setFieldsTouched({
        credentials: true,
      });
    },
  };
}

function getStep(config, i18n) {
  if (!config.ask_credential_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 4,
    name: i18n._(t`Credentials`),
    component: <CredentialsStep i18n={i18n} />,
    enableNext: true,
  };
}

function getInitialValues(config, loadedResource, currentResource) {
  if (!config.ask_credential_on_launch) {
    return {};
  }
  return {
    credentials:
      currentResource?.summary_fields?.credentials ||
      loadedResource?.summary_fields?.credentials ||
      [],
  };
}
