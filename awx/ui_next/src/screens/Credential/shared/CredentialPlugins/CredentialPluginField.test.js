import React from 'react';
import { Formik } from 'formik';
import { TextInput } from '@patternfly/react-core';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import CredentialPluginField from './CredentialPluginField';

const fieldOptions = {
  id: 'username',
  label: 'Username',
  type: 'string',
};

jest.mock('../../../../api');

describe('<CredentialPluginField />', () => {
  let wrapper;
  describe('No plugin configured', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            inputs: {
              username: '',
            },
          }}
        >
          {() => (
            <CredentialPluginField
              fieldOptions={fieldOptions}
              isDisabled={false}
              isRequired={false}
            >
              <TextInput id="credential-username" />
            </CredentialPluginField>
          )}
        </Formik>
      );
    });

    test('renders the expected content', () => {
      expect(wrapper.find('input').length).toBe(1);
      expect(wrapper.find('KeyIcon').length).toBe(1);
      expect(wrapper.find('CredentialPluginSelected').length).toBe(0);
    });

    test('clicking plugin button shows plugin prompt', async () => {
      expect(wrapper.find('CredentialPluginPrompt').length).toBe(0);
      await act(async () => {
        wrapper.find('KeyIcon').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('CredentialPluginPrompt').length).toBe(1);
    });
  });

  describe('Plugin already configured', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            inputs: {
              username: {
                credential: {
                  id: 1,
                  name: 'CyberArk Cred',
                  cloud: false,
                  credential_type_id: 20,
                  kind: 'conjur',
                },
              },
            },
          }}
        >
          {() => (
            <CredentialPluginField
              fieldOptions={fieldOptions}
              isDisabled={false}
              isRequired={false}
            >
              <TextInput id="credential-username" />
            </CredentialPluginField>
          )}
        </Formik>
      );
    });

    test('renders the expected content', () => {
      expect(wrapper.find('CredentialPluginPrompt').length).toBe(0);
      expect(wrapper.find('input').length).toBe(0);
      expect(wrapper.find('KeyIcon').length).toBe(1);
      expect(wrapper.find('CredentialPluginSelected').length).toBe(1);
    });
  });
});
