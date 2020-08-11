import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import {
  CredentialsAPI,
  CredentialInputSourcesAPI,
  CredentialTypesAPI,
} from '../../../api';
import CredentialAdd from './CredentialAdd';

jest.mock('../../../api');

CredentialTypesAPI.read.mockResolvedValue({
  data: {
    results: [
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

  describe('Initial GET request succeeds', () => {
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

    test('handleSubmit should call the api and redirect to details page', async () => {
      await waitForElement(wrapper, 'isLoading', el => el.length === 0);
      await act(async () => {
        wrapper.find('CredentialForm').prop('onSubmit')({
          user: 1,
          name: 'foo',
          description: 'bar',
          credential_type: '1',
          inputs: {
            username: {
              credential: {
                id: 1,
                name: 'Some cred',
              },
              inputs: {
                foo: 'bar',
              },
            },
            password: 'foo',
            ssh_key_data: 'bar',
            ssh_public_key_data: 'baz',
            ssh_key_unlock: 'foobar',
            become_method: '',
            become_username: '',
            become_password: '',
          },
          passwordPrompts: {
            become_password: true,
          },
        });
      });
      expect(CredentialsAPI.create).toHaveBeenCalledWith({
        user: 1,
        name: 'foo',
        description: 'bar',
        credential_type: '1',
        inputs: {
          password: 'foo',
          ssh_key_data: 'bar',
          ssh_public_key_data: 'baz',
          ssh_key_unlock: 'foobar',
          become_method: '',
          become_username: '',
          become_password: 'ASK',
        },
      });
      expect(CredentialInputSourcesAPI.create).toHaveBeenCalledWith({
        input_field_name: 'username',
        metadata: {
          foo: 'bar',
        },
        source_credential: 1,
        target_credential: 13,
      });
      expect(history.location.pathname).toBe('/credentials/13/details');
    });

    test('handleCancel should return the user back to the credentials list', async () => {
      await waitForElement(wrapper, 'isLoading', el => el.length === 0);
      await act(async () => {
        wrapper.find('Button[aria-label="Cancel"]').simulate('click');
      });
      wrapper.update();
      expect(history.location.pathname).toEqual('/credentials');
    });
  });

  describe('Initial GET request fails', () => {
    test('shows error when initial GET request fails', async () => {
      CredentialTypesAPI.read.mockRejectedValue(new Error());
      history = createMemoryHistory({ initialEntries: ['/credentials'] });
      await act(async () => {
        wrapper = mountWithContexts(<CredentialAdd />, {
          context: { router: { history } },
        });
      });
      wrapper.update();
      expect(wrapper.find('ContentError').length).toBe(1);
      wrapper.unmount();
    });
  });
});
