import React from 'react';
import { t } from '@lingui/macro';

import CredentialsStep from './CredentialsStep';

const STEP_ID = 'credentials';

export default function useCredentialsStep(launchConfig, resource, i18n) {
  return {
    step: getStep(launchConfig, i18n),
    initialValues: getInitialValues(launchConfig, resource),
    validate: () => ({}),
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

function getStep(launchConfig, i18n) {
  if (!launchConfig.ask_credential_on_launch) {
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

function getInitialValues(launchConfig, resource) {
  if (!launchConfig.ask_credential_on_launch) {
    return {};
  }

  return {
    credentials: resource?.summary_fields?.credentials || [],
  };
}
