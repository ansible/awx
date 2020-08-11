import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import CredentialsStep from './CredentialsStep';
import { CredentialsAPI, CredentialTypesAPI } from '../../../api';

jest.mock('../../../api/models/CredentialTypes');
jest.mock('../../../api/models/Credentials');

const types = [
  { id: 1, kind: 'ssh', name: 'SSH' },
  { id: 2, kind: 'cloud', name: 'Ansible Tower' },
  { id: 3, kind: 'vault', name: 'Vault' },
];

const credentials = [
  { id: 1, kind: 'cloud', name: 'Cred 1', url: 'www.google.com' },
  { id: 2, kind: 'ssh', name: 'Cred 2', url: 'www.google.com' },
  { id: 3, kind: 'Ansible', name: 'Cred 3', url: 'www.google.com' },
  { id: 4, kind: 'Machine', name: 'Cred 4', url: 'www.google.com' },
  { id: 5, kind: 'Machine', name: 'Cred 5', url: 'www.google.com' },
];

describe('CredentialsStep', () => {
  beforeEach(() => {
    CredentialTypesAPI.loadAllTypes.mockResolvedValue(types);
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: credentials,
        count: 5,
      },
    });
    CredentialsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  test('should load credentials', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <CredentialsStep />
        </Formik>
      );
    });
    wrapper.update();

    expect(CredentialsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('OptionsList').prop('options')).toEqual(credentials);
  });

  test('should load credentials for selected type', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <CredentialsStep />
        </Formik>
      );
    });
    wrapper.update();

    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 1,
      order_by: 'name',
      page: 1,
      page_size: 5,
    });

    await act(async () => {
      wrapper.find('AnsibleSelect').invoke('onChange')({}, 2);
    });
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 2,
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
});
