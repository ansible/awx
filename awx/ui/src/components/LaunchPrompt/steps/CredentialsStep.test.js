import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { CredentialsAPI, CredentialTypesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { createMemoryHistory } from 'history';
import CredentialsStep from './CredentialsStep';

jest.mock('../../../api/models/CredentialTypes');
jest.mock('../../../api/models/Credentials');

const types = [
  { id: 1, kind: 'ssh', name: 'SSH', url: '/api/v2/credential_types/1/' },
  { id: 3, kind: 'vault', name: 'Vault', url: '/api/v2/credential_types/3/' },
  {
    id: 5,
    name: 'Amazon Web Services',
    kind: 'cloud',
    url: '/api/v2/credential_types/5/',
  },
  {
    id: 9,
    name: 'Google Compute Engine',
    kind: 'cloud',
    url: '/api/v2/credential_types/9/',
  },
];

const credentials = [
  {
    id: 1,
    kind: 'aws',
    name: 'Cred 1',
    credential_type: 5,
    url: '/api/v2/credentials/1/',
    inputs: {},
  },
  {
    id: 2,
    kind: 'ssh',
    name: 'Cred 2',
    credential_type: 1,
    url: '/api/v2/credentials/2/',
    inputs: {
      password: 'ASK',
    },
  },
  {
    id: 3,
    kind: 'gce',
    name: 'Cred 3',
    credential_type: 9,
    url: '/api/v2/credentials/3/',
    inputs: {},
  },
  {
    id: 4,
    kind: 'ssh',
    name: 'Cred 4',
    credential_type: 1,
    url: '/api/v2/credentials/4/',
    inputs: {},
  },
  {
    id: 5,
    kind: 'ssh',
    name: 'Cred 5',
    credential_type: 1,
    url: '/api/v2/credentials/5/',
    inputs: {},
  },
  {
    id: 33,
    kind: 'vault',
    name: 'Cred 33',
    credential_type: 3,
    url: '/api/v2/credentials/33/',
    inputs: {
      vault_id: 'foo',
    },
    summary_fields: {
      credential_type: {
        name: 'Vault',
      },
    },
  },
  {
    id: 34,
    kind: 'vault',
    name: 'Cred 34',
    credential_type: 3,
    url: '/api/v2/credentials/34/',
    inputs: {
      vault_id: 'bar',
    },
    summary_fields: {
      credential_type: {
        name: 'Vault',
      },
    },
  },
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
          <CredentialsStep allowCredentialsWithPasswords />
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
          <CredentialsStep allowCredentialsWithPasswords />
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
      wrapper.find('AnsibleSelect').invoke('onChange')({}, 3);
    });
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 3,
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });

  test('should reset query params (credential.page) when selected credential type is changed', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: [
        '?credential.page=2&credential.page_size=5&credential.order_by=name',
      ],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <CredentialsStep allowCredentialsWithPasswords />
        </Formik>,
        {
          context: { router: { history } },
        }
      );
    });
    wrapper.update();

    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 1,
      order_by: 'name',
      page: 2,
      page_size: 5,
    });

    await act(async () => {
      wrapper.find('AnsibleSelect').invoke('onChange')({}, 3);
    });
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 3,
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });

  test("error should be shown when a credential that prompts for passwords is selected on a step that doesn't allow it", async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            credentials: [],
          }}
        >
          <CredentialsStep allowCredentialsWithPasswords={false} />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(0);
    await act(async () => {
      wrapper.find('td#check-action-item-2').find('input').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(1);
    expect(wrapper.find('Alert').text().includes('Cred 2')).toBe(true);
  });

  test('error should be toggled when default machine credential is removed and then replaced', async () => {
    let wrapper;
    const selectedCredentials = [
      {
        id: 5,
        kind: 'ssh',
        name: 'Cred 5',
        credential_type: 1,
        url: '/api/v2/credentials/5/',
        inputs: {},
        summary_fields: {
          credential_type: {
            name: 'Machine',
          },
        },
      },
    ];
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            credentials: selectedCredentials,
          }}
        >
          <CredentialsStep
            allowCredentialsWithPasswords={false}
            defaultCredentials={selectedCredentials}
          />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(0);
    expect(wrapper.find('CredentialChip').length).toBe(1);
    await act(async () => {
      wrapper.find('button#remove_credential-chip-5').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(1);
    expect(wrapper.find('Alert').text().includes('Machine')).toBe(true);
    await act(async () => {
      wrapper.find('td#check-action-item-5').find('input').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(0);
  });

  test('error should be toggled when default vault credential is removed and then replaced', async () => {
    let wrapper;
    const selectedCredentials = [
      {
        id: 33,
        kind: 'vault',
        name: 'Cred 33',
        credential_type: 3,
        url: '/api/v2/credentials/33/',
        inputs: {
          vault_id: 'foo',
        },
        summary_fields: {
          credential_type: {
            name: 'Vault',
          },
        },
      },
      {
        id: 34,
        kind: 'vault',
        name: 'Cred 34',
        credential_type: 3,
        url: '/api/v2/credentials/34/',
        inputs: {
          vault_id: 'bar',
        },
        summary_fields: {
          credential_type: {
            name: 'Vault',
          },
        },
      },
    ];
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            credentials: selectedCredentials,
          }}
        >
          <CredentialsStep
            allowCredentialsWithPasswords={false}
            defaultCredentials={selectedCredentials}
          />
        </Formik>
      );
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(0);
    expect(wrapper.find('CredentialChip').length).toBe(2);
    await act(async () => {
      wrapper.find('button#remove_credential-chip-33').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CredentialChip').length).toBe(1);
    expect(wrapper.find('Alert').length).toBe(1);
    expect(wrapper.find('Alert').text().includes('Vault | foo')).toBe(true);
    await act(async () => {
      wrapper.find('AnsibleSelect').invoke('onChange')({}, 3);
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('td#check-action-item-33').find('input').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('Alert').length).toBe(0);
  });
});
