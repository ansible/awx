import React from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import CredentialPasswordsStep from './CredentialPasswordsStep';
import StepName from './StepName';

const STEP_ID = 'credentialPasswords';

const isValueMissing = (val) => !val || val === '';

export default function useCredentialPasswordsStep(
  launchConfig,

  showStep,
  visitedSteps
) {
  const { values, setFieldError } = useFormikContext();
  const hasError =
    Object.keys(visitedSteps).includes(STEP_ID) &&
    checkForError(launchConfig, values);

  return {
    step: showStep
      ? {
          id: STEP_ID,
          name: (
            <StepName hasErrors={hasError} id="credential-passwords-step">
              {t`Credential passwords`}
            </StepName>
          ),
          component: <CredentialPasswordsStep launchConfig={launchConfig} />,
          enableNext: true,
        }
      : null,
    initialValues: getInitialValues(launchConfig, values.credentials),
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

      if (
        !launchConfig.ask_credential_on_launch &&
        launchConfig.passwords_needed_to_start
      ) {
        launchConfig.passwords_needed_to_start.forEach((password) => {
          if (isValueMissing(values.credential_passwords[password])) {
            setPasswordFieldError(`credential_passwords['${password}']`);
          }
        });
      } else if (values.credentials) {
        values.credentials.forEach((credential) => {
          if (!credential.inputs) {
            const launchConfigCredential =
              launchConfig.defaults.credentials.find(
                (defaultCred) => defaultCred.id === credential.id
              );

            if (launchConfigCredential?.passwords_needed.length > 0) {
              launchConfigCredential.passwords_needed.forEach((password) => {
                if (isValueMissing(values.credential_passwords[password])) {
                  setPasswordFieldError(`credential_passwords['${password}']`);
                }
              });
            }
          } else {
            if (
              credential?.inputs?.password === 'ASK' &&
              isValueMissing(values.credential_passwords.ssh_password)
            ) {
              setPasswordFieldError('credential_passwords.ssh_password');
            }

            if (
              credential?.inputs?.become_password === 'ASK' &&
              isValueMissing(values.credential_passwords.become_password)
            ) {
              setPasswordFieldError('credential_passwords.become_password');
            }

            if (
              credential?.inputs?.ssh_key_unlock === 'ASK' &&
              isValueMissing(values.credential_passwords.ssh_key_unlock)
            ) {
              setPasswordFieldError('credential_passwords.ssh_key_unlock');
            }

            if (
              credential?.inputs?.vault_password === 'ASK' &&
              isValueMissing(
                values.credential_passwords[
                  `vault_password${
                    credential.inputs.vault_id !== ''
                      ? `.${credential.inputs.vault_id}`
                      : ''
                  }`
                ]
              )
            ) {
              setPasswordFieldError(
                `credential_passwords['vault_password${
                  credential.inputs.vault_id !== ''
                    ? `.${credential.inputs.vault_id}`
                    : ''
                }']`
              );
            }
          }
        });
      }
    },
  };
}

function getInitialValues(launchConfig, selectedCredentials = []) {
  const initialValues = {
    credential_passwords: {},
  };

  if (!launchConfig) {
    return initialValues;
  }

  if (
    !launchConfig.ask_credential_on_launch &&
    launchConfig.passwords_needed_to_start
  ) {
    launchConfig.passwords_needed_to_start.forEach((password) => {
      initialValues.credential_passwords[password] = '';
    });
    return initialValues;
  }

  selectedCredentials.forEach((credential) => {
    if (!credential.inputs) {
      const launchConfigCredential = launchConfig.defaults.credentials.find(
        (defaultCred) => defaultCred.id === credential.id
      );

      if (launchConfigCredential?.passwords_needed.length > 0) {
        launchConfigCredential.passwords_needed.forEach((password) => {
          initialValues.credential_passwords[password] = '';
        });
      }
    } else {
      if (credential?.inputs?.password === 'ASK') {
        initialValues.credential_passwords.ssh_password = '';
      }

      if (credential?.inputs?.become_password === 'ASK') {
        initialValues.credential_passwords.become_password = '';
      }

      if (credential?.inputs?.ssh_key_unlock === 'ASK') {
        initialValues.credential_passwords.ssh_key_unlock = '';
      }

      if (credential?.inputs?.vault_password === 'ASK') {
        if (!credential.inputs.vault_id || credential.inputs.vault_id === '') {
          initialValues.credential_passwords.vault_password = '';
        } else {
          initialValues.credential_passwords[
            `vault_password.${credential.inputs.vault_id}`
          ] = '';
        }
      }
    }
  });

  return initialValues;
}

function checkForError(launchConfig, values) {
  let hasError = false;

  if (
    !launchConfig.ask_credential_on_launch &&
    launchConfig.passwords_needed_to_start
  ) {
    launchConfig.passwords_needed_to_start.forEach((password) => {
      if (isValueMissing(values.credential_passwords[password])) {
        hasError = true;
      }
    });
  } else if (values.credentials) {
    values.credentials.forEach((credential) => {
      if (!credential.inputs) {
        const launchConfigCredential = launchConfig.defaults.credentials.find(
          (defaultCred) => defaultCred.id === credential.id
        );

        if (launchConfigCredential?.passwords_needed.length > 0) {
          launchConfigCredential.passwords_needed.forEach((password) => {
            if (isValueMissing(values.credential_passwords[password])) {
              hasError = true;
            }
          });
        }
      } else {
        if (
          credential?.inputs?.password === 'ASK' &&
          isValueMissing(values.credential_passwords.ssh_password)
        ) {
          hasError = true;
        }

        if (
          credential?.inputs?.become_password === 'ASK' &&
          isValueMissing(values.credential_passwords.become_password)
        ) {
          hasError = true;
        }

        if (
          credential?.inputs?.ssh_key_unlock === 'ASK' &&
          isValueMissing(values.credential_passwords.ssh_key_unlock)
        ) {
          hasError = true;
        }

        if (
          credential?.inputs?.vault_password === 'ASK' &&
          isValueMissing(
            values.credential_passwords[
              `vault_password${
                credential.inputs.vault_id !== ''
                  ? `.${credential.inputs.vault_id}`
                  : ''
              }`
            ]
          )
        ) {
          hasError = true;
        }
      }
    });
  }

  return hasError;
}
