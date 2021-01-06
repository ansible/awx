import getCredentialPasswords from './getCredentialPasswords';

describe('getCredentialPasswords', () => {
  test('should handle ssh password', () => {
    expect(
      getCredentialPasswords({
        credentialPasswordSsh: 'foobar',
      })
    ).toEqual({
      ssh_password: 'foobar',
    });
  });
  test('should handle become password', () => {
    expect(
      getCredentialPasswords({
        credentialPasswordPrivilegeEscalation: 'foobar',
      })
    ).toEqual({
      become_password: 'foobar',
    });
  });
  test('should handle ssh key unlock', () => {
    expect(
      getCredentialPasswords({
        credentialPasswordPrivateKeyPassphrase: 'foobar',
      })
    ).toEqual({
      ssh_key_unlock: 'foobar',
    });
  });
  test('should handle vault password with identifier', () => {
    expect(
      getCredentialPasswords({
        credentialPasswordVault_1: 'foobar',
      })
    ).toEqual({
      'vault_password.1': 'foobar',
    });
  });
  test('should handle vault password without identifier', () => {
    expect(
      getCredentialPasswords({
        credentialPasswordVault_: 'foobar',
      })
    ).toEqual({
      vault_password: 'foobar',
    });
  });
  test('should handle all password types', () => {
    expect(
      getCredentialPasswords({
        credentialPasswordSsh: '1',
        credentialPasswordPrivilegeEscalation: '2',
        credentialPasswordPrivateKeyPassphrase: '3',
        credentialPasswordVault_: '4',
        credentialPasswordVault_1: '5',
      })
    ).toEqual({
      ssh_password: '1',
      become_password: '2',
      ssh_key_unlock: '3',
      vault_password: '4',
      'vault_password.1': '5',
    });
  });
});
