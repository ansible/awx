import React from 'react';
import { useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import StepName from '../LaunchPrompt/steps/StepName';
import CredentialPasswordsStep from '../LaunchPrompt/steps/CredentialPasswordsStep';

const STEP_ID = 'credentialPasswords';

const isValueMissing = (val) => !val || val === '';

export default function useCredentialPasswordsStep(showStep, visitedSteps) {
  const { values, setFieldError } = useFormikContext();
  const hasError =
    showStep &&
    Object.keys(visitedSteps).includes(STEP_ID) &&
    checkForError(values);
  return {
    step: showStep
      ? {
          id: STEP_ID,
          name: (
            <StepName hasErrors={hasError} id="credential-passwords-step">
              {t`Credential passwords`}
            </StepName>
          ),
          component: <CredentialPasswordsStep launchConfig={{}} />,
          enableNext: true,
        }
      : null,
    isReady: true,
    contentError: null,
    hasError,
    setTouched: (setFieldTouched) => {
      Object.keys(values.credential_passwords).forEach((credentialValueKey) =>
        setFieldTouched(
          `credential_passwords['${credentialValueKey}']`,
          true,
          false
        )
      );
    },
    validate: () => {
      const setPasswordFieldError = (fieldName) => {
        setFieldError(fieldName, t`This field may not be blank`);
      };

      Object.entries(values.credentials[0].inputs).forEach(([key, value]) => {
        if (
          value === 'ASK' &&
          isValueMissing(
            key === 'password'
              ? values.credential_passwords.ssh_password
              : values.credential_passwords[key]
          )
        ) {
          setPasswordFieldError(
            key === 'password'
              ? `credential_passwords.ssh_password`
              : `credential_passwords.${key}`
          );
        }
      });
    },
  };
}

function checkForError(values) {
  let hasError = false;
  Object.entries(values.credentials[0]?.inputs).forEach(([key, value]) => {
    if (
      value === 'ASK' &&
      isValueMissing(
        key === 'password'
          ? values.credential_passwords.ssh_password
          : values.credential_passwords[key]
      )
    ) {
      hasError = true;
    }
  });
  return hasError;
}
