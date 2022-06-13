import React from 'react';
import { useField } from 'formik';
import { t } from '@lingui/macro';
import StepName from '../LaunchPrompt/steps/StepName';
import AdHocCredentialStep from './AdHocCredentialStep';

const STEP_ID = 'credentials';
export default function useAdHocExecutionEnvironmentStep(
  visited,
  credentialTypeId
) {
  const [field, meta, helpers] = useField('credentials');
  const hasError =
    Object.keys(visited).includes('credentials') &&
    !field.value.length &&
    meta.touched;

  return {
    step: {
      id: STEP_ID,
      key: 3,
      name: (
        <StepName hasErrors={hasError} id="credential-step">
          {t`Credential`}
        </StepName>
      ),
      component: <AdHocCredentialStep credentialTypeId={credentialTypeId} />,
      enableNext: true,
      nextButtonText: t`Next`,
    },
    hasError,
    validate: () => {
      if (!meta.value.length) {
        helpers.setError('A credential must be selected');
      }
    },
    setTouched: (setFieldTouched) => {
      setFieldTouched('credentials', true, false);
    },
  };
}
