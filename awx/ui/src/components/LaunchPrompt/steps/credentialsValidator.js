import { t } from '@lingui/macro';

const credentialPromptsForPassword = (credential) =>
  credential?.inputs?.password === 'ASK' ||
  credential?.inputs?.ssh_key_unlock === 'ASK' ||
  credential?.inputs?.become_password === 'ASK' ||
  credential?.inputs?.vault_password === 'ASK';

export default function credentialsValidator(
  allowCredentialsWithPasswords,
  selectedCredentials,
  defaultCredentials = []
) {
  if (defaultCredentials.length > 0 && selectedCredentials) {
    const missingCredentialTypes = [];
    defaultCredentials.forEach((defaultCredential) => {
      if (
        !selectedCredentials.find(
          (selectedCredential) =>
            (selectedCredential?.credential_type ===
              defaultCredential?.credential_type &&
              !selectedCredential.inputs?.vault_id &&
              !defaultCredential.inputs?.vault_id) ||
            (defaultCredential.inputs?.vault_id &&
              selectedCredential.inputs?.vault_id ===
                defaultCredential.inputs?.vault_id)
        )
      ) {
        missingCredentialTypes.push(
          defaultCredential.inputs?.vault_id
            ? `${defaultCredential.summary_fields.credential_type.name} | ${defaultCredential.inputs.vault_id}`
            : defaultCredential.summary_fields.credential_type.name
        );
      }
    });

    if (missingCredentialTypes.length > 0) {
      return t`Job Template default credentials must be replaced with one of the same type.  Please select a credential for the following types in order to proceed: ${missingCredentialTypes.join(
        ', '
      )}`;
    }
  }

  if (!allowCredentialsWithPasswords && selectedCredentials) {
    const credentialsThatPrompt = [];
    selectedCredentials.forEach((selectedCredential) => {
      if (credentialPromptsForPassword(selectedCredential)) {
        credentialsThatPrompt.push(selectedCredential.name);
      }
    });
    if (credentialsThatPrompt.length > 0) {
      return t`Credentials that require passwords on launch are not permitted.  Please remove or replace the following credentials with a credential of the same type in order to proceed: ${credentialsThatPrompt.join(
        ', '
      )}`;
    }
  }

  return undefined;
}
