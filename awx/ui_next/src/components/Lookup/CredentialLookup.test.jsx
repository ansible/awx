import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import CredentialLookup, { _CredentialLookup } from './CredentialLookup';
import { CredentialsAPI } from '@api';

jest.mock('@api');

describe('CredentialLookup', () => {
  let wrapper;

  beforeEach(() => {
    CredentialsAPI.read.mockResolvedValueOnce({
      data: {
        results: [
          { id: 1, kind: 'cloud', name: 'Cred 1', url: 'www.google.com' },
          { id: 2, kind: 'ssh', name: 'Cred 2', url: 'www.google.com' },
          { id: 3, kind: 'Ansible', name: 'Cred 3', url: 'www.google.com' },
          { id: 4, kind: 'Machine', name: 'Cred 4', url: 'www.google.com' },
          { id: 5, kind: 'Machine', name: 'Cred 5', url: 'www.google.com' },
        ],
        count: 5,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should render successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialLookup
          credentialTypeId={1}
          label="Foo"
          onChange={() => {}}
        />
      );
    });
    expect(wrapper.find('CredentialLookup')).toHaveLength(1);
  });

  test('should fetch credentials', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialLookup
          credentialTypeId={1}
          label="Foo"
          onChange={() => {}}
        />
      );
    });
    expect(CredentialsAPI.read).toHaveBeenCalledTimes(1);
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 1,
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });

  test('should display label', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialLookup
          credentialTypeId={1}
          label="Foo"
          onChange={() => {}}
        />
      );
    });
    const title = wrapper.find('FormGroup .pf-c-form__label-text');
    expect(title.text()).toEqual('Foo');
  });

  test('should define default value for function props', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialLookup
          credentialTypeId={1}
          label="Foo"
          onChange={() => {}}
        />
      );
    });
    expect(_CredentialLookup.defaultProps.onBlur).toBeInstanceOf(Function);
    expect(_CredentialLookup.defaultProps.onBlur).not.toThrow();
  });
});
