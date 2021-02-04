import React from 'react';
import { t } from '@lingui/macro';
import CredentialsStep from './CredentialsStep';
import StepName from './StepName';

const STEP_ID = 'credentials';

export default function useCredentialsStep(launchConfig, resource, i18n) {
  return {
    step: getStep(launchConfig, i18n),
    initialValues: getInitialValues(launchConfig, resource),
    isReady: true,
    contentError: null,
    hasError: false,
    setTouched: setFieldTouched => {
      setFieldTouched('credentials', true, false);
    },
    validate: () => {},
  };
}

function getStep(launchConfig, i18n) {
  if (!launchConfig.ask_credential_on_launch) {
    return null;
  }
  return {
    id: STEP_ID,
    key: 4,
    name: (
      <StepName hasErrors={false} id="credentials-step">
        {i18n._(t`Credentials`)}
      </StepName>
    ),
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
