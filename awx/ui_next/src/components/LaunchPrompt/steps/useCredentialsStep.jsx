import React from 'react';
import { t } from '@lingui/macro';
import CredentialsStep from './CredentialsStep';

const STEP_ID = 'credentials';

export default function useCredentialsStep(config, resource, i18n) {
  const validate = values => {
    const errors = {};
    if (!values.credentials || !values.credentials.length) {
      errors.credentials = i18n._(t`Credentials must be selected`);
    }
    return errors;
  };

  return {
    step: getStep(config, i18n),
    initialValues: getInitialValues(config, resource),
    validate,
    isReady: true,
    error: null,
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
