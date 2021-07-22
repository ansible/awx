import React from 'react';

import { t } from '@lingui/macro';
import { Form } from '@patternfly/react-core';
import { useFormikContext } from 'formik';
import { PasswordField } from '../../FormField';

function CredentialPasswordsStep({ launchConfig }) {
  const {
    values: { credentials },
  } = useFormikContext();

  const vaultsThatPrompt = [];
  let showcredentialPasswordSsh = false;
  let showcredentialPasswordPrivilegeEscalation = false;
  let showcredentialPasswordPrivateKeyPassphrase = false;

  if (
    !launchConfig.ask_credential_on_launch &&
    launchConfig.passwords_needed_to_start
  ) {
    launchConfig.passwords_needed_to_start.forEach((password) => {
      if (password === 'ssh_password') {
        showcredentialPasswordSsh = true;
      } else if (password === 'become_password') {
        showcredentialPasswordPrivilegeEscalation = true;
      } else if (password === 'ssh_key_unlock') {
        showcredentialPasswordPrivateKeyPassphrase = true;
      } else if (password.startsWith('vault_password')) {
        const vaultId = password.split(/\.(.+)/)[1] || '';
        vaultsThatPrompt.push(vaultId);
      }
    });
  } else if (credentials) {
    credentials.forEach((credential) => {
      if (!credential.inputs) {
        const launchConfigCredential = launchConfig.defaults.credentials.find(
          (defaultCred) => defaultCred.id === credential.id
        );

        if (launchConfigCredential?.passwords_needed.length > 0) {
          if (
            launchConfigCredential.passwords_needed.includes('ssh_password')
          ) {
            showcredentialPasswordSsh = true;
          }
          if (
            launchConfigCredential.passwords_needed.includes('become_password')
          ) {
            showcredentialPasswordPrivilegeEscalation = true;
          }
          if (
            launchConfigCredential.passwords_needed.includes('ssh_key_unlock')
          ) {
            showcredentialPasswordPrivateKeyPassphrase = true;
          }

          const vaultPasswordIds = launchConfigCredential.passwords_needed
            .filter((passwordNeeded) =>
              passwordNeeded.startsWith('vault_password')
            )
            .map((vaultPassword) => vaultPassword.split(/\.(.+)/)[1] || '');

          vaultsThatPrompt.push(...vaultPasswordIds);
        }
      } else {
        if (credential?.inputs?.password === 'ASK') {
          showcredentialPasswordSsh = true;
        }

        if (credential?.inputs?.become_password === 'ASK') {
          showcredentialPasswordPrivilegeEscalation = true;
        }

        if (credential?.inputs?.ssh_key_unlock === 'ASK') {
          showcredentialPasswordPrivateKeyPassphrase = true;
        }

        if (credential?.inputs?.vault_password === 'ASK') {
          vaultsThatPrompt.push(credential.inputs.vault_id);
        }
      }
    });
  }

  return (
    <Form
      onSubmit={(e) => {
        e.preventDefault();
      }}
    >
      {showcredentialPasswordSsh && (
        <PasswordField
          id="launch-ssh-password"
          label={t`SSH password`}
          name="credential_passwords.ssh_password"
          isRequired
        />
      )}
      {showcredentialPasswordPrivateKeyPassphrase && (
        <PasswordField
          id="launch-private-key-passphrase"
          label={t`Private key passphrase`}
          name="credential_passwords.ssh_key_unlock"
          isRequired
        />
      )}
      {showcredentialPasswordPrivilegeEscalation && (
        <PasswordField
          id="launch-privilege-escalation-password"
          label={t`Privilege escalation password`}
          name="credential_passwords.become_password"
          isRequired
        />
      )}
      {vaultsThatPrompt.map((credId) => (
        <PasswordField
          id={`launch-vault-password-${credId}`}
          key={credId}
          label={
            credId === '' ? t`Vault password` : t`Vault password | ${credId}`
          }
          name={`credential_passwords['vault_password${
            credId !== '' ? `.${credId}` : ''
          }']`}
          isRequired
        />
      ))}
    </Form>
  );
}

export default CredentialPasswordsStep;
