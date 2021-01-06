export default function getCredentialPasswords(values) {
  const credentialPasswords = {};
  Object.keys(values)
    .filter(valueKey => valueKey.startsWith('credentialPassword'))
    .forEach(credentialValueKey => {
      if (credentialValueKey === 'credentialPasswordSsh') {
        credentialPasswords.ssh_password = values[credentialValueKey];
      }

      if (credentialValueKey === 'credentialPasswordPrivilegeEscalation') {
        credentialPasswords.become_password = values[credentialValueKey];
      }

      if (credentialValueKey === 'credentialPasswordPrivateKeyPassphrase') {
        credentialPasswords.ssh_key_unlock = values[credentialValueKey];
      }

      if (credentialValueKey.startsWith('credentialPasswordVault_')) {
        const vaultId = credentialValueKey.split('credentialPasswordVault_')[1];
        if (vaultId.length > 0) {
          credentialPasswords[`vault_password.${vaultId}`] =
            values[credentialValueKey];
        } else {
          credentialPasswords.vault_password = values[credentialValueKey];
        }
      }
    });
  return credentialPasswords;
}
