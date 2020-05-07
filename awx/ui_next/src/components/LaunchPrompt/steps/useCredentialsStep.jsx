import React from 'react';
import { t } from '@lingui/macro';
import CredentialsStep from './CredentialsStep';

const STEP_ID = 'credentials';

export default function useCredentialsStep(
  config,
  resource,
  visitedSteps,
  i18n
) {
  const validate = () => {
    return {};
  };

  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, resource),
    validate,
    isReady: true,
    error: null,
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
    name: i18n._(t`Credentials`),
    component: <CredentialsStep i18n={i18n} />,
  };
}

function getInitialValues(config, resource) {
  if (!config.ask_credential_on_launch) {
    return {};
  }
  return {
    credentials: resource?.summary_fields?.credentials || [],
  };
}
