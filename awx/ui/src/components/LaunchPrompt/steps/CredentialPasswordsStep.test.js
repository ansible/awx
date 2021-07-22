import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import CredentialPasswordsStep from './CredentialPasswordsStep';

describe('CredentialPasswordsStep', () => {
  describe('JT default credentials (no credential replacement) and creds are promptable', () => {
    test('should render ssh password field when JT has default machine cred', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [
                    {
                      id: 1,
                      passwords_needed: ['ssh_password'],
                    },
                  ],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render become password field when JT has default machine cred', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [
                    {
                      id: 1,
                      passwords_needed: ['become_password'],
                    },
                  ],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render private key passphrase field when JT has default machine cred', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                defaults: {
                  ask_credential_on_launch: true,
                  credentials: [
                    {
                      id: 1,
                      passwords_needed: ['ssh_key_unlock'],
                    },
                  ],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render vault password field when JT has default vault cred', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [
                    {
                      id: 1,
                      passwords_needed: ['vault_password.1'],
                    },
                  ],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-vault-password-1')
      ).toHaveLength(1);
    });
    test('should render all password field when JT has default vault cred and machine cred', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                },
                {
                  id: 2,
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [
                    {
                      id: 1,
                      passwords_needed: [
                        'ssh_password',
                        'become_password',
                        'ssh_key_unlock',
                      ],
                    },
                    {
                      id: 2,
                      passwords_needed: ['vault_password.1'],
                    },
                  ],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-vault-password-1')
      ).toHaveLength(1);
    });
  });
  describe('Credentials have been replaced and creds are promptable', () => {
    test('should render ssh password field when replacement machine cred prompts for it', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                  inputs: {
                    password: 'ASK',
                    become_password: null,
                    ssh_key_unlock: null,
                    vault_password: null,
                  },
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render become password field when replacement machine cred prompts for it', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                  inputs: {
                    password: null,
                    become_password: 'ASK',
                    ssh_key_unlock: null,
                    vault_password: null,
                  },
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render private key passphrase field when replacement machine cred prompts for it', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                  inputs: {
                    password: null,
                    become_password: null,
                    ssh_key_unlock: 'ASK',
                    vault_password: null,
                  },
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render vault password field when replacement vault cred prompts for it', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                  inputs: {
                    password: null,
                    become_password: null,
                    ssh_key_unlock: null,
                    vault_password: 'ASK',
                    vault_id: 'foobar',
                  },
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-vault-password-foobar')
      ).toHaveLength(1);
    });
    test('should render all password fields when replacement vault and machine creds prompt for it', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik
            initialValues={{
              credentials: [
                {
                  id: 1,
                  inputs: {
                    password: 'ASK',
                    become_password: 'ASK',
                    ssh_key_unlock: 'ASK',
                  },
                },
                {
                  id: 2,
                  inputs: {
                    password: null,
                    become_password: null,
                    ssh_key_unlock: null,
                    vault_password: 'ASK',
                    vault_id: 'foobar',
                  },
                },
              ],
            }}
          >
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: true,
                defaults: {
                  credentials: [],
                },
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-vault-password-foobar')
      ).toHaveLength(1);
    });
  });
  describe('Credentials have been replaced and creds are not promptable', () => {
    test('should render ssh password field when required', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik initialValues={{}}>
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: false,
                passwords_needed_to_start: ['ssh_password'],
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render become password field when required', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik initialValues={{}}>
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: false,
                passwords_needed_to_start: ['become_password'],
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render private key passphrase field when required', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik initialValues={{}}>
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: false,
                passwords_needed_to_start: ['ssh_key_unlock'],
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(0);
    });
    test('should render vault password field when required', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik initialValues={{}}>
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: false,
                passwords_needed_to_start: ['vault_password.foobar'],
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(0);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-vault-password-foobar')
      ).toHaveLength(1);
    });
    test('should render all password fields when required', async () => {
      let wrapper;
      await act(async () => {
        wrapper = mountWithContexts(
          <Formik initialValues={{}}>
            <CredentialPasswordsStep
              launchConfig={{
                ask_credential_on_launch: false,
                passwords_needed_to_start: [
                  'ssh_password',
                  'become_password',
                  'ssh_key_unlock',
                  'vault_password.foobar',
                ],
              }}
            />
          </Formik>
        );
      });

      expect(wrapper.find('PasswordField#launch-ssh-password')).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-private-key-passphrase')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-privilege-escalation-password')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField[id^="launch-vault-password-"]')
      ).toHaveLength(1);
      expect(
        wrapper.find('PasswordField#launch-vault-password-foobar')
      ).toHaveLength(1);
    });
  });
});
