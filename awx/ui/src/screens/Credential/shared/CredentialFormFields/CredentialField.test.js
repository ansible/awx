import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import credentialTypes from '../data.credentialTypes.json';
import CredentialField from './CredentialField';

const credentialType = credentialTypes.find((type) => type.id === 5);
const fieldOptions = {
  id: 'password',
  label: 'Secret Key',
  type: 'string',
  secret: true,
};

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/credentials/3/edit',
  }),
}));
describe('<CredentialField />', () => {
  let wrapper;
  test('renders correctly without initial value', () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          passwordPrompts: {},
          inputs: {
            password: '',
          },
        }}
      >
        {() => (
          <CredentialField
            fieldOptions={fieldOptions}
            credentialType={credentialType}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('CredentialField').length).toBe(1);
    expect(wrapper.find('PasswordInput').length).toBe(1);
    expect(wrapper.find('TextInput').props().isDisabled).toBe(false);
    expect(wrapper.find('KeyIcon').length).toBe(1);
    expect(wrapper.find('PficonHistoryIcon').length).toBe(0);
  });

  test('renders correctly with initial value', () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          passwordPrompts: {},
          inputs: {
            password: '$encrypted$',
          },
        }}
      >
        {() => (
          <CredentialField
            fieldOptions={fieldOptions}
            credentialType={credentialType}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('CredentialField').length).toBe(1);
    expect(wrapper.find('PasswordInput').length).toBe(1);
    expect(wrapper.find('TextInput').props().isDisabled).toBe(true);
    expect(wrapper.find('TextInput').props().value).toBe('');
    expect(wrapper.find('TextInput').props().placeholder).toBe('ENCRYPTED');
    expect(wrapper.find('KeyIcon').length).toBe(1);
    expect(wrapper.find('PficonHistoryIcon').length).toBe(1);
  });

  test('replace/revert button behaves as expected', async () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          passwordPrompts: {},
          inputs: {
            password: '$encrypted$',
          },
        }}
      >
        {() => (
          <CredentialField
            fieldOptions={fieldOptions}
            credentialType={credentialType}
          />
        )}
      </Formik>
    );
    expect(
      wrapper.find('Tooltip#credential-password-replace-tooltip').props()
        .content
    ).toBe('Replace');
    expect(wrapper.find('TextInput').props().isDisabled).toBe(true);
    wrapper.find('PficonHistoryIcon').simulate('click');
    await act(async () => {
      wrapper.update();
    });
    expect(
      wrapper.find('Tooltip#credential-password-replace-tooltip').props()
        .content
    ).toBe('Revert');
    expect(wrapper.find('TextInput').props().isDisabled).toBe(false);
    expect(wrapper.find('TextInput').props().value).toBe('');
    expect(wrapper.find('TextInput').props().placeholder).toBe(undefined);
    wrapper.find('PficonHistoryIcon').simulate('click');
    await act(async () => {
      wrapper.update();
    });
    expect(
      wrapper.find('Tooltip#credential-password-replace-tooltip').props()
        .content
    ).toBe('Replace');
    expect(wrapper.find('TextInput').props().isDisabled).toBe(true);
    expect(wrapper.find('TextInput').props().value).toBe('');
    expect(wrapper.find('TextInput').props().placeholder).toBe('ENCRYPTED');
  });
  test('Should check to see if the ability to edit vault ID is disabled after creation.', () => {
    const vaultCredential = credentialTypes.find((type) => type.id === 3);
    const vaultFieldOptions = {
      id: 'vault_id',
      label: 'Vault Identifier',
      type: 'string',
      secret: true,
    };
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          passwordPrompts: {},
          inputs: {
            password: 'password',
            vault_id: 'vault_id',
          },
        }}
      >
        {() => (
          <CredentialField
            fieldOptions={vaultFieldOptions}
            credentialType={vaultCredential}
          />
        )}
      </Formik>
    );
    expect(wrapper.find('CredentialInput').props().isDisabled).toBe(true);
    expect(wrapper.find('KeyIcon').length).toBe(1);
  });
});
