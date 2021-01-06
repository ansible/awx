import React from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import CredentialPasswordsStep from './CredentialPasswordsStep';
import StepName from './StepName';

const STEP_ID = 'credentialPasswords';

const isValueMissing = val => {
  return !val || val === '';
};

export default function useCredentialPasswordsStep(
  launchConfig,
  i18n,
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
              {i18n._(t`Credential passwords`)}
            </StepName>
          ),
          component: (
            <CredentialPasswordsStep launchConfig={launchConfig} i18n={i18n} />
          ),
          enableNext: true,
        }
      : null,
    initialValues: getInitialValues(launchConfig, values.credentials),
    isReady: true,
    contentError: null,
    hasError,
    setTouched: setFieldTouched => {
      Object.keys(values)
        .filter(valueKey => valueKey.startsWith('credentialPassword'))
        .forEach(credentialValueKey =>
          setFieldTouched(credentialValueKey, true, false)
        );
    },
    validate: () => {
      const setPasswordFieldError = fieldName => {
        setFieldError(fieldName, i18n._(t`This field may not be blank`));
      };

      const {
        credentialPasswordSsh,
        credentialPasswordPrivilegeEscalation,
        credentialPasswordPrivateKeyPassphrase,
      } = values;

      if (
        !launchConfig.ask_credential_on_launch &&
        launchConfig.passwords_needed_to_start
      ) {
        launchConfig.passwords_needed_to_start.forEach(password => {
          if (
            password === 'ssh_password' &&
            isValueMissing(credentialPasswordSsh)
          ) {
            setPasswordFieldError('credentialPasswordSsh');
          } else if (
            password === 'become_password' &&
            isValueMissing(credentialPasswordPrivilegeEscalation)
          ) {
            setPasswordFieldError('credentialPasswordPrivilegeEscalation');
          } else if (
            password === 'ssh_key_unlock' &&
            isValueMissing(credentialPasswordPrivateKeyPassphrase)
          ) {
            setPasswordFieldError('credentialPasswordPrivateKeyPassphrase');
          } else if (password.startsWith('vault_password')) {
            const vaultId = password.split(/\.(.+)/)[1] || '';
            if (isValueMissing(values[`credentialPasswordVault_${vaultId}`])) {
              setPasswordFieldError(`credentialPasswordVault_${vaultId}`);
            }
          }
        });
      } else if (values.credentials) {
        values.credentials.forEach(credential => {
          if (!credential.inputs) {
            const launchConfigCredential = launchConfig.defaults.credentials.find(
              defaultCred => defaultCred.id === credential.id
            );

            if (launchConfigCredential?.passwords_needed.length > 0) {
              if (
                launchConfigCredential.passwords_needed.includes(
                  'ssh_password'
                ) &&
                isValueMissing(credentialPasswordSsh)
              ) {
                setPasswordFieldError('credentialPasswordSsh');
              }
              if (
                launchConfigCredential.passwords_needed.includes(
                  'become_password'
                ) &&
                isValueMissing(credentialPasswordPrivilegeEscalation)
              ) {
                setPasswordFieldError('credentialPasswordPrivilegeEscalation');
              }
              if (
                launchConfigCredential.passwords_needed.includes(
                  'ssh_key_unlock'
                ) &&
                isValueMissing(credentialPasswordPrivateKeyPassphrase)
              ) {
                setPasswordFieldError('credentialPasswordPrivateKeyPassphrase');
              }

              launchConfigCredential.passwords_needed
                .filter(passwordNeeded =>
                  passwordNeeded.startsWith('vault_password')
                )
                .map(vaultPassword => vaultPassword.split(/\.(.+)/)[1] || '')
                .forEach(vaultId => {
                  if (
                    isValueMissing(values[`credentialPasswordVault_${vaultId}`])
                  ) {
                    setPasswordFieldError(`credentialPasswordVault_${vaultId}`);
                  }
                });
            }
          } else {
            if (
              credential?.inputs?.password === 'ASK' &&
              isValueMissing(credentialPasswordSsh)
            ) {
              setPasswordFieldError('credentialPasswordSsh');
            }

            if (
              credential?.inputs?.become_password === 'ASK' &&
              isValueMissing(credentialPasswordPrivilegeEscalation)
            ) {
              setPasswordFieldError('credentialPasswordPrivilegeEscalation');
            }

            if (
              credential?.inputs?.ssh_key_unlock === 'ASK' &&
              isValueMissing(credentialPasswordPrivateKeyPassphrase)
            ) {
              setPasswordFieldError('credentialPasswordPrivateKeyPassphrase');
            }

            if (
              credential?.inputs?.vault_password === 'ASK' &&
              isValueMissing(
                values[`credentialPasswordVault_${credential.inputs.vault_id}`]
              )
            ) {
              setPasswordFieldError(
                `credentialPasswordVault_${credential.inputs.vault_id}`
              );
            }
          }
        });
      }
    },
  };
}

function getInitialValues(launchConfig, selectedCredentials = []) {
  const initialValues = {};

  if (!launchConfig) {
    return initialValues;
  }

  if (
    !launchConfig.ask_credential_on_launch &&
    launchConfig.passwords_needed_to_start
  ) {
    launchConfig.passwords_needed_to_start.forEach(password => {
      if (password === 'ssh_password') {
        initialValues.credentialPasswordSsh = '';
      } else if (password === 'become_password') {
        initialValues.credentialPasswordPrivilegeEscalation = '';
      } else if (password === 'ssh_key_unlock') {
        initialValues.credentialPasswordPrivateKeyPassphrase = '';
      } else if (password.startsWith('vault_password')) {
        const vaultId = password.split(/\.(.+)/)[1] || '';
        initialValues[`credentialPasswordVault_${vaultId}`] = '';
      }
    });
    return initialValues;
  }

  selectedCredentials.forEach(credential => {
    if (!credential.inputs) {
      const launchConfigCredential = launchConfig.defaults.credentials.find(
        defaultCred => defaultCred.id === credential.id
      );

      if (launchConfigCredential?.passwords_needed.length > 0) {
        if (launchConfigCredential.passwords_needed.includes('ssh_password')) {
          initialValues.credentialPasswordSsh = '';
        }
        if (
          launchConfigCredential.passwords_needed.includes('become_password')
        ) {
          initialValues.credentialPasswordPrivilegeEscalation = '';
        }
        if (
          launchConfigCredential.passwords_needed.includes('ssh_key_unlock')
        ) {
          initialValues.credentialPasswordPrivateKeyPassphrase = '';
        }

        const vaultPasswordIds = launchConfigCredential.passwords_needed
          .filter(passwordNeeded => passwordNeeded.startsWith('vault_password'))
          .map(vaultPassword => vaultPassword.split(/\.(.+)/)[1] || '');

        vaultPasswordIds.forEach(vaultPasswordId => {
          initialValues[`credentialPasswordVault_${vaultPasswordId}`] = '';
        });
      }
    } else {
      if (credential?.inputs?.password === 'ASK') {
        initialValues.credentialPasswordSsh = '';
      }

      if (credential?.inputs?.become_password === 'ASK') {
        initialValues.credentialPasswordPrivilegeEscalation = '';
      }

      if (credential?.inputs?.ssh_key_unlock === 'ASK') {
        initialValues.credentialPasswordPrivateKeyPassphrase = '';
      }

      if (credential?.inputs?.vault_password === 'ASK') {
        initialValues[`credentialPasswordVault_${credential.inputs.vault_id}`] =
          '';
      }
    }
  });

  return initialValues;
}

function checkForError(launchConfig, values) {
  const {
    credentialPasswordSsh,
    credentialPasswordPrivilegeEscalation,
    credentialPasswordPrivateKeyPassphrase,
  } = values;

  let hasError = false;

  if (
    !launchConfig.ask_credential_on_launch &&
    launchConfig.passwords_needed_to_start
  ) {
    launchConfig.passwords_needed_to_start.forEach(password => {
      if (
        (password === 'ssh_password' &&
          isValueMissing(credentialPasswordSsh)) ||
        (password === 'become_password' &&
          isValueMissing(credentialPasswordPrivilegeEscalation)) ||
        (password === 'ssh_key_unlock' &&
          isValueMissing(credentialPasswordPrivateKeyPassphrase))
      ) {
        hasError = true;
      } else if (password.startsWith('vault_password')) {
        const vaultId = password.split(/\.(.+)/)[1] || '';
        if (isValueMissing(values[`credentialPasswordVault_${vaultId}`])) {
          hasError = true;
        }
      }
    });
  } else if (values.credentials) {
    values.credentials.forEach(credential => {
      if (!credential.inputs) {
        const launchConfigCredential = launchConfig.defaults.credentials.find(
          defaultCred => defaultCred.id === credential.id
        );

        if (launchConfigCredential?.passwords_needed.length > 0) {
          if (
            (launchConfigCredential.passwords_needed.includes('ssh_password') &&
              isValueMissing(credentialPasswordSsh)) ||
            (launchConfigCredential.passwords_needed.includes(
              'become_password'
            ) &&
              isValueMissing(credentialPasswordPrivilegeEscalation)) ||
            (launchConfigCredential.passwords_needed.includes(
              'ssh_key_unlock'
            ) &&
              isValueMissing(credentialPasswordPrivateKeyPassphrase))
          ) {
            hasError = true;
          }

          launchConfigCredential.passwords_needed
            .filter(passwordNeeded =>
              passwordNeeded.startsWith('vault_password')
            )
            .map(vaultPassword => vaultPassword.split(/\.(.+)/)[1] || '')
            .forEach(vaultId => {
              if (
                isValueMissing(values[`credentialPasswordVault_${vaultId}`])
              ) {
                hasError = true;
              }
            });
        }
      } else {
        if (
          (credential?.inputs?.password === 'ASK' &&
            isValueMissing(credentialPasswordSsh)) ||
          (credential?.inputs?.become_password === 'ASK' &&
            isValueMissing(credentialPasswordPrivilegeEscalation)) ||
          (credential?.inputs?.ssh_key_unlock === 'ASK' &&
            isValueMissing(credentialPasswordPrivateKeyPassphrase))
        ) {
          hasError = true;
        }

        if (
          credential?.inputs?.vault_password === 'ASK' &&
          isValueMissing(
            values[`credentialPasswordVault_${credential.inputs.vault_id}`]
          )
        ) {
          hasError = true;
        }
      }
    });
  }

  return hasError;
}
