import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../../testUtils/enzymeHelpers';
import { CredentialsAPI, CredentialTypesAPI } from '../../../../../api';
import selectedCredential from '../../data.cyberArkCredential.json';
import azureVaultCredential from '../../data.azureVaultCredential.json';
import hashiCorpCredential from '../../data.hashiCorpCredential.json';
import CredentialPluginPrompt from './CredentialPluginPrompt';

jest.mock('../../../../../api/models/Credentials');
jest.mock('../../../../../api/models/CredentialTypes');

CredentialsAPI.test.mockResolvedValue({});

CredentialsAPI.read.mockResolvedValue({
  data: {
    count: 3,
    results: [selectedCredential, azureVaultCredential, hashiCorpCredential],
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

CredentialTypesAPI.readDetail.mockResolvedValue({
  data: {
    id: 20,
    type: 'credential_type',
    url: '/api/v2/credential_types/20/',
    related: {
      named_url:
        '/api/v2/credential_types/CyberArk Conjur Secret Lookup+external/',
      credentials: '/api/v2/credential_types/20/credentials/',
      activity_stream: '/api/v2/credential_types/20/activity_stream/',
    },
    summary_fields: { user_capabilities: { edit: false, delete: false } },
    created: '2020-05-18T21:53:35.398260Z',
    modified: '2020-05-18T21:54:05.451444Z',
    name: 'CyberArk Conjur Secret Lookup',
    description: '',
    kind: 'external',
    namespace: 'conjur',
    managed_by_tower: true,
    inputs: {
      fields: [
        { id: 'url', label: 'Conjur URL', type: 'string', format: 'url' },
        { id: 'api_key', label: 'API Key', type: 'string', secret: true },
        { id: 'account', label: 'Account', type: 'string' },
        { id: 'username', label: 'Username', type: 'string' },
        {
          id: 'cacert',
          label: 'Public Key Certificate',
          type: 'string',
          multiline: true,
        },
      ],
      metadata: [
        {
          id: 'secret_path',
          label: 'Secret Identifier',
          type: 'string',
          help_text: 'The identifier for the secret e.g., /some/identifier',
        },
        {
          id: 'secret_version',
          label: 'Secret Version',
          type: 'string',
          help_text:
            'Used to specify a specific secret version (if left empty, the latest version will be used).',
        },
      ],
      required: ['url', 'api_key', 'account', 'username'],
    },
    injectors: {},
  },
});

describe('<CredentialPluginPrompt />', () => {
  describe('Plugin not configured', () => {
    let wrapper;
    const onClose = jest.fn();
    const onSubmit = jest.fn();
    beforeAll(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialPluginPrompt onClose={onClose} onSubmit={onSubmit} />
        );
      });
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('should render Wizard with all steps', async () => {
      const wizard = await waitForElement(wrapper, 'Wizard');
      const steps = wizard.prop('steps');

      expect(steps).toHaveLength(2);
      expect(steps[0].name).toEqual('Credential');
      expect(steps[1].name).toEqual('Metadata');
    });
    test('credentials step renders correctly', () => {
      expect(wrapper.find('CredentialsStep').length).toBe(1);
      expect(wrapper.find('DataListItem').length).toBe(3);
      expect(
        wrapper.find('Radio').filterWhere(radio => radio.isChecked).length
      ).toBe(0);
    });
    test('next button disabled until credential selected', () => {
      expect(wrapper.find('Button[children="Next"]').prop('isDisabled')).toBe(
        true
      );
    });
    test('clicking cancel button calls correct function', () => {
      wrapper.find('Button[children="Cancel"]').simulate('click');
      expect(onClose).toHaveBeenCalledTimes(1);
    });
    test('clicking credential row enables next button', async () => {
      await act(async () => {
        wrapper
          .find('Radio')
          .at(0)
          .invoke('onChange')(true);
      });
      wrapper.update();
      expect(
        wrapper
          .find('Radio')
          .at(0)
          .prop('isChecked')
      ).toBe(true);
      expect(wrapper.find('Button[children="Next"]').prop('isDisabled')).toBe(
        false
      );
    });
    test('clicking next button shows metatdata step', async () => {
      await act(async () => {
        wrapper.find('Button[children="Next"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('MetadataStep').length).toBe(1);
      expect(wrapper.find('FormField').length).toBe(2);
    });
    test('submit button calls correct function with parameters', async () => {
      await act(async () => {
        wrapper.find('input#credential-secret_path').simulate('change', {
          target: { value: '/foo/bar', name: 'secret_path' },
        });
      });
      await act(async () => {
        wrapper.find('input#credential-secret_version').simulate('change', {
          target: { value: '9000', name: 'secret_version' },
        });
      });
      await act(async () => {
        wrapper.find('Button[children="OK"]').simulate('click');
      });
      // expect(wrapper.debug()).toBe(false);
      // wrapper.find('Button[children="OK"]').simulate('click');
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          credential: selectedCredential,
          secret_path: '/foo/bar',
          secret_version: '9000',
        }),
        expect.anything()
      );
    });
  });

  describe('Plugin already configured', () => {
    let wrapper;
    const onClose = jest.fn();
    const onSubmit = jest.fn();
    beforeAll(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <CredentialPluginPrompt
            onClose={onClose}
            onSubmit={onSubmit}
            initialValues={{
              credential: selectedCredential,
              inputs: {
                secret_path: '/foo/bar',
                secret_version: '9000',
              },
            }}
          />
        );
      });
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('should render Wizard with all steps', async () => {
      const wizard = await waitForElement(wrapper, 'Wizard');
      const steps = wizard.prop('steps');

      expect(steps).toHaveLength(2);
      expect(steps[0].name).toEqual('Credential');
      expect(steps[1].name).toEqual('Metadata');
    });
    test('credentials step renders correctly', () => {
      expect(wrapper.find('CredentialsStep').length).toBe(1);
      expect(wrapper.find('DataListItem').length).toBe(3);
      expect(
        wrapper
          .find('Radio')
          .at(0)
          .prop('isChecked')
      ).toBe(true);
      expect(wrapper.find('Button[children="Next"]').prop('isDisabled')).toBe(
        false
      );
    });
    test('metadata step renders correctly', async () => {
      await act(async () => {
        wrapper.find('Button[children="Next"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('MetadataStep').length).toBe(1);
      expect(wrapper.find('FormField').length).toBe(2);
      expect(wrapper.find('input#credential-secret_path').prop('value')).toBe(
        '/foo/bar'
      );
      expect(
        wrapper.find('input#credential-secret_version').prop('value')
      ).toBe('9000');
    });
    test('clicking Test button makes correct call', async () => {
      await act(async () => {
        wrapper.find('Button[children="Test"]').simulate('click');
      });
      expect(CredentialsAPI.test).toHaveBeenCalledWith(1, {
        metadata: { secret_path: '/foo/bar', secret_version: '9000' },
      });
    });
  });
});
