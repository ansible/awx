import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { CredentialsAPI, CredentialTypesAPI } from '../../../api';
import ExternalTestModal from './ExternalTestModal';
import credentialTypesArr from './data.credentialTypes.json';

jest.mock('../../../api/models/Credentials');
jest.mock('../../../api/models/CredentialTypes');

const credentialType = credentialTypesArr.find(
  credType => credType.namespace === 'hashivault_kv'
);

const credentialFormValues = {
  name: 'Foobar',
  credential_type: credentialType.id,
  inputs: {
    api_version: 'v2',
    token: '$encrypted$',
    url: 'http://hashivault:8200',
  },
};

const credential = {
  id: 1,
  name: 'A credential',
  credential_type: credentialType.id,
};

describe('<ExternalTestModal />', () => {
  let wrapper;
  afterEach(() => wrapper.unmount());
  test('should display metadata fields correctly', async () => {
    wrapper = mountWithContexts(
      <ExternalTestModal
        credentialType={credentialType}
        credentialFormValues={credentialFormValues}
        onClose={jest.fn()}
      />
    );
    expect(wrapper.find('FormField').length).toBe(5);
    expect(wrapper.find('input#credential-secret_backend').length).toBe(1);
    expect(wrapper.find('input#credential-secret_path').length).toBe(1);
    expect(wrapper.find('input#credential-auth_path').length).toBe(1);
    expect(wrapper.find('input#credential-secret_key').length).toBe(1);
    expect(wrapper.find('input#credential-secret_version').length).toBe(1);
  });
  test('should make the test request correctly when testing an existing credential', async () => {
    wrapper = mountWithContexts(
      <ExternalTestModal
        credential={credential}
        credentialType={credentialType}
        credentialFormValues={credentialFormValues}
        onClose={jest.fn()}
      />
    );
    await act(async () => {
      wrapper.find('input#credential-secret_path').simulate('change', {
        target: { value: '/secret/foo/bar/baz', name: 'secret_path' },
      });
      wrapper.find('input#credential-secret_key').simulate('change', {
        target: { value: 'password', name: 'secret_key' },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[children="Run"]').simulate('click');
    });
    expect(CredentialsAPI.test).toHaveBeenCalledWith(1, {
      inputs: {
        api_version: 'v2',
        cacert: undefined,
        role_id: undefined,
        secret_id: undefined,
        token: '$encrypted$',
        url: 'http://hashivault:8200',
      },
      metadata: {
        auth_path: '',
        secret_backend: '',
        secret_key: 'password',
        secret_path: '/secret/foo/bar/baz',
        secret_version: '',
      },
    });
  });
  test('should make the test request correctly when testing a new credential', async () => {
    wrapper = mountWithContexts(
      <ExternalTestModal
        credentialType={credentialType}
        credentialFormValues={credentialFormValues}
        onClose={jest.fn()}
      />
    );
    await act(async () => {
      wrapper.find('input#credential-secret_path').simulate('change', {
        target: { value: '/secret/foo/bar/baz', name: 'secret_path' },
      });
      wrapper.find('input#credential-secret_key').simulate('change', {
        target: { value: 'password', name: 'secret_key' },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[children="Run"]').simulate('click');
    });
    expect(CredentialTypesAPI.test).toHaveBeenCalledWith(21, {
      inputs: {
        api_version: 'v2',
        cacert: undefined,
        role_id: undefined,
        secret_id: undefined,
        token: '$encrypted$',
        url: 'http://hashivault:8200',
      },
      metadata: {
        auth_path: '',
        secret_backend: '',
        secret_key: 'password',
        secret_path: '/secret/foo/bar/baz',
        secret_version: '',
      },
    });
  });
  test('should display the alert after a successful test', async () => {
    CredentialTypesAPI.test.mockResolvedValue({});
    wrapper = mountWithContexts(
      <ExternalTestModal
        credentialType={credentialType}
        credentialFormValues={credentialFormValues}
        onClose={jest.fn()}
      />
    );
    await act(async () => {
      wrapper.find('input#credential-secret_path').simulate('change', {
        target: { value: '/secret/foo/bar/baz', name: 'secret_path' },
      });
      wrapper.find('input#credential-secret_key').simulate('change', {
        target: { value: 'password', name: 'secret_key' },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[children="Run"]').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(1);
    expect(wrapper.find('Alert').props().variant).toBe('success');
  });
  test('should display the alert after a failed test', async () => {
    CredentialTypesAPI.test.mockRejectedValue({
      inputs: `HTTP 404
        {"errors":["no handler for route '/secret/foo/bar/baz'"]}
      `,
    });
    wrapper = mountWithContexts(
      <ExternalTestModal
        credentialType={credentialType}
        credentialFormValues={credentialFormValues}
        onClose={jest.fn()}
      />
    );
    await act(async () => {
      wrapper.find('input#credential-secret_path').simulate('change', {
        target: { value: '/secret/foo/bar/baz', name: 'secret_path' },
      });
      wrapper.find('input#credential-secret_key').simulate('change', {
        target: { value: 'password', name: 'secret_key' },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[children="Run"]').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(1);
    expect(wrapper.find('Alert').props().variant).toBe('danger');
  });
});
