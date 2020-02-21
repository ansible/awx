import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import { CredentialsAPI, CredentialTypesAPI } from '@api';
import CredentialAdd from './CredentialAdd';

jest.mock('@api');

CredentialTypesAPI.read.mockResolvedValue({
  data: {
    results: [
      {
        id: 2,
        type: 'credential_type',
        url: '/api/v2/credential_types/2/',
        related: {
          credentials: '/api/v2/credential_types/2/credentials/',
          activity_stream: '/api/v2/credential_types/2/activity_stream/',
        },
        summary_fields: {
          user_capabilities: {
            edit: false,
            delete: false,
          },
        },
        created: '2020-02-12T19:42:43.551238Z',
        modified: '2020-02-12T19:43:03.164800Z',
        name: 'Source Control',
        description: '',
        kind: 'scm',
        namespace: 'scm',
        managed_by_tower: true,
        inputs: {
          fields: [
            {
              id: 'username',
              label: 'Username',
              type: 'string',
            },
            {
              id: 'password',
              label: 'Password',
              type: 'string',
              secret: true,
            },
            {
              id: 'ssh_key_data',
              label: 'SCM Private Key',
              type: 'string',
              format: 'ssh_private_key',
              secret: true,
              multiline: true,
            },
            {
              id: 'ssh_key_unlock',
              label: 'Private Key Passphrase',
              type: 'string',
              secret: true,
            },
          ],
        },
        injectors: {},
      },
      {
        id: 1,
        type: 'credential_type',
        url: '/api/v2/credential_types/1/',
        related: {
          credentials: '/api/v2/credential_types/1/credentials/',
          activity_stream: '/api/v2/credential_types/1/activity_stream/',
        },
        summary_fields: {
          user_capabilities: {
            edit: false,
            delete: false,
          },
        },
        created: '2020-02-12T19:42:43.539626Z',
        modified: '2020-02-12T19:43:03.159739Z',
        name: 'Machine',
        description: '',
        kind: 'ssh',
        namespace: 'ssh',
        managed_by_tower: true,
        inputs: {
          fields: [
            {
              id: 'username',
              label: 'Username',
              type: 'string',
            },
            {
              id: 'password',
              label: 'Password',
              type: 'string',
              secret: true,
              ask_at_runtime: true,
            },
            {
              id: 'ssh_key_data',
              label: 'SSH Private Key',
              type: 'string',
              format: 'ssh_private_key',
              secret: true,
              multiline: true,
            },
            {
              id: 'ssh_public_key_data',
              label: 'Signed SSH Certificate',
              type: 'string',
              multiline: true,
              secret: true,
            },
            {
              id: 'ssh_key_unlock',
              label: 'Private Key Passphrase',
              type: 'string',
              secret: true,
              ask_at_runtime: true,
            },
            {
              id: 'become_method',
              label: 'Privilege Escalation Method',
              type: 'string',
              help_text:
                'Specify a method for "become" operations. This is equivalent to specifying the --become-method Ansible parameter.',
            },
            {
              id: 'become_username',
              label: 'Privilege Escalation Username',
              type: 'string',
            },
            {
              id: 'become_password',
              label: 'Privilege Escalation Password',
              type: 'string',
              secret: true,
              ask_at_runtime: true,
            },
          ],
        },
        injectors: {},
      },
    ],
  },
});

CredentialsAPI.create.mockResolvedValue({ data: { id: 13 } });

describe('<CredentialAdd />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({ initialEntries: ['/credentials'] });
    await act(async () => {
      wrapper = mountWithContexts(<CredentialAdd />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('handleSubmit should call the api and redirect to details page', async () => {
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);

    wrapper.find('CredentialForm').prop('onSubmit')({
      user: 1,
      organization: null,
      name: 'foo',
      description: 'bar',
      credential_type: '2',
      inputs: {},
    });
    await sleep(1);
    expect(CredentialsAPI.create).toHaveBeenCalledWith({
      user: 1,
      organization: null,
      name: 'foo',
      description: 'bar',
      credential_type: '2',
      inputs: {},
    });
    expect(history.location.pathname).toBe('/credentials/13/details');
  });

  test('handleCancel should return the user back to the inventories list', async () => {
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);
    wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/credentials');
  });
});
